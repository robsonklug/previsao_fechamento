import * as XLSX from 'xlsx';
import { InsertOpportunity } from '../drizzle/schema';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

/**
 * Interface para dados brutos da planilha
 */
interface RawOpportunity {
  ID?: string | number;
  'NOME DA OPORTUNIDADE'?: string;
  ORIGEM?: string;
  'NOME DO CLIENTE'?: string;
  CNPJ?: string;
  'ETAPA ATUAL'?: string;
  ESN?: string;
  GSN?: string;
  'TIPO DE ATUAÇÃO'?: string;
  'FEELING FECHAMENTO'?: number;
  'PREVISÃO DE FECHAMENTO'?: string | Date;
  'PRODUTO DA OPORTUNIDADE'?: string;
  'PRODUTO SUGERIDO'?: string;
  'VALOR SUGERIDO'?: number;
  'DATA CICLO DE BUSCA'?: string | Date;
  [key: string]: any;
}

/**
 * Parsear planilha Excel e extrair oportunidades
 */
export async function parseOpportunitiesFromExcel(buffer: Buffer): Promise<RawOpportunity[]> {
  try {
    const workbook = XLSX.read(buffer, { type: 'buffer' });
    
    // Tentar encontrar a aba "Dados Sintéticos" ou usar a primeira aba
    let sheetName = workbook.SheetNames[0];
    if (workbook.SheetNames.includes('Dados Sintéticos')) {
      sheetName = 'Dados Sintéticos';
    }

    const worksheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(worksheet) as RawOpportunity[];

    return data;
  } catch (error) {
    console.error('Error parsing Excel file:', error);
    throw new Error('Failed to parse Excel file');
  }
}

/**
 * Chamar o script Python para fazer previsões com o modelo Gradient Boosting
 */
async function callPythonPredictor(opportunities: RawOpportunity[]): Promise<Record<string, number>> {
  return new Promise((resolve, reject) => {
    // Criar arquivo temporário com os dados
    const tmpFile = path.join(os.tmpdir(), `opportunities_${Date.now()}.json`);
    const outputFile = path.join(os.tmpdir(), `predictions_${Date.now()}.json`);

    try {
      // Escrever dados em arquivo JSON
      fs.writeFileSync(tmpFile, JSON.stringify(opportunities));

      // Chamar script Python
      const pythonProcess = spawn('python3.11', [
        '/home/ubuntu/predict.py',
        tmpFile,
        outputFile,
      ]);

      let stderr = '';
      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        try {
          if (code !== 0) {
            reject(new Error(`Python script failed with code ${code}: ${stderr}`));
            return;
          }

          // Ler resultados
          const predictions = JSON.parse(fs.readFileSync(outputFile, 'utf-8'));

          // Limpar arquivos temporários
          fs.unlinkSync(tmpFile);
          fs.unlinkSync(outputFile);

          resolve(predictions);
        } catch (error) {
          reject(error);
        }
      });
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Gerar previsões para oportunidades usando o modelo de IA
 */
export async function predictOpportunitiesClosure(
  rawOpportunities: RawOpportunity[]
): Promise<InsertOpportunity[]> {
  try {
    // Chamar o preditor Python
    const predictions = await callPythonPredictor(rawOpportunities);

    // Processar oportunidades com previsões
    const today = new Date();
    const processedOpportunities: InsertOpportunity[] = [];

    rawOpportunities.forEach((rawOpp, index) => {
      const daysToClose = predictions[index.toString()] || 0;
      const estimatedCloseDate = new Date(today);
      estimatedCloseDate.setDate(estimatedCloseDate.getDate() + daysToClose);

      const opportunity: Partial<InsertOpportunity> = {
        opportunityId: String(rawOpp.ID || ''),
        opportunityName: rawOpp['NOME DA OPORTUNIDADE'] || '',
        origin: rawOpp.ORIGEM || '',
        clientName: rawOpp['NOME DO CLIENTE'] || '',
        cnpj: rawOpp.CNPJ || '',
        currentStage: rawOpp['ETAPA ATUAL'] || '',
        esn: rawOpp.ESN || '',
        gsn: rawOpp.GSN || '',
        activityType: rawOpp['TIPO DE ATUAÇÃO'] || '',
        closingFeeling: rawOpp['FEELING FECHAMENTO'] || 0,
        humanForecastDate: rawOpp['PREVISÃO DE FECHAMENTO'] 
          ? new Date(rawOpp['PREVISÃO DE FECHAMENTO']) 
          : undefined,
        productOpportunity: rawOpp['PRODUTO DA OPORTUNIDADE'] || '',
        suggestedProduct: rawOpp['PRODUTO SUGERIDO'] || '',
        suggestedValue: rawOpp['VALOR SUGERIDO'] 
          ? String(rawOpp['VALOR SUGERIDO']) 
          : '0',
        predictedDaysToClose: daysToClose,
        estimatedCloseDate: estimatedCloseDate,
      };

      processedOpportunities.push(opportunity as InsertOpportunity);
    });

    return processedOpportunities as InsertOpportunity[];
  } catch (error) {
    console.error('Error predicting opportunities:', error);
    throw new Error(`Failed to predict opportunities: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}
