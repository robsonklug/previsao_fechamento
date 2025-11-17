import pandas as pd
import requests
import re
import time
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import numpy as np

# --- Variáveis de Configuração ---
FILE_PATH = r"C:\Klug\Python\Projeto_15 - Fechemanto Oportunidade\vendas.xlsx"
API_URL = "https://brasilapi.com.br/api/cnpj/v1/"
ENRICHMENT_COLUMNS = [
    'CNAE_FISCAL', 'PORTE', 'NATUREZA_JURIDICA', 
    'DATA_INICIO_ATIVIDADE', 'SITUACAO_CADASTRAL', 'UF', 'MUNICIPIO'
]
CNPJ_COLUMN = 'CNPJ'

# --- Funções de Enriquecimento ---

def clean_cnpj(cnpj):
    """Remove formatação do CNPJ, deixando apenas números."""
    if pd.isna(cnpj):
        return None
    cleaned = re.sub(r'[^0-9]', '', str(cnpj))
    return cleaned if len(cleaned) == 14 else None

def get_cnpj_data(cnpj_clean):
    """Consulta a API BrasilAPI para obter dados do CNPJ."""
    if not cnpj_clean or len(cnpj_clean) != 14:
        return None
    
    url = f"{API_URL}{cnpj_clean}"
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            print(f"CNPJ {cnpj_clean} não encontrado (404).")
            return None
        
        if response.status_code == 400:
            print(f"CNPJ {cnpj_clean} inválido ou não encontrado (400).")
            return None
        
        if response.status_code == 429:
            # Se for 429, levanta exceção para que o loop principal possa lidar com o erro
            response.raise_for_status()
        
        response.raise_for_status() # Levanta exceção para códigos de status HTTP ruins (4xx ou 5xx)
        data = response.json()
        print(f"Dados do CNPJ {cnpj_clean} obtidos com sucesso.")
        
        # Extrair os campos desejados
        extracted_data = {
            'CNAE_FISCAL': data.get('cnae_fiscal'),
            'PORTE': data.get('porte'),
            'NATUREZA_JURIDICA': data.get('natureza_juridica'),
            'DATA_INICIO_ATIVIDADE': data.get('data_inicio_atividade'),
            'SITUACAO_CADASTRAL': data.get('situacao_cadastral'),
            'UF': data.get('uf'),
            'MUNICIPIO': data.get('municipio')
        }
        return extracted_data
    except requests.exceptions.HTTPError as e:
        # Captura erros HTTP que não são 404 (já tratado)
        print(f"Erro HTTP ao consultar API para CNPJ {cnpj_clean}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        # Captura outros erros de requisição (timeout, conexão, etc.)
        print(f"Erro de requisição ao consultar API para CNPJ {cnpj_clean}: {e}")
        return None
    except Exception as e:
        # Captura erros inesperados (ex: erro ao processar JSON)
        print(f"Erro inesperado ao processar dados do CNPJ {cnpj_clean}: {e}")
        return None

def enrich_data(df):
    """Enriquece o DataFrame com dados do CNPJ, usando cache e lógica de preenchimento."""
    
    # 1. Garantir que as colunas de enriquecimento existam
    for col in ENRICHMENT_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # 2. Limpar a coluna CNPJ
    df['CNPJ_CLEAN'] = df[CNPJ_COLUMN].apply(clean_cnpj)
    
    # 3. Identificar linhas que precisam de enriquecimento (onde CNAE_FISCAL está vazio)
    # Usamos .isna() para verificar valores NaN ou None
    df_to_enrich = df[df['CNAE_FISCAL'].isna()].copy()
    
    if df_to_enrich.empty:
        print("Todos os dados de CNPJ já estão preenchidos. Pulando consulta à API.")
        return df

    print(f"Iniciando enriquecimento para {len(df_to_enrich)} CNPJs...")
    
    # 4. Processar CNPJs únicos para otimizar chamadas (cache implícito)
    unique_cnpjs = df_to_enrich['CNPJ_CLEAN'].dropna().unique()
    cnpj_cache = {}
    
    for i, cnpj in enumerate(unique_cnpjs):
        if cnpj not in cnpj_cache:
            print(f"Consultando API para CNPJ {cnpj} ({i+1}/{len(unique_cnpjs)})...")
            try:
                data = get_cnpj_data(cnpj)
                cnpj_cache[cnpj] = data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"Erro 429 (Too Many Requests) para CNPJ {cnpj}. Pausando por 60 segundos...")
                    time.sleep(60)
                    # Tenta novamente o mesmo CNPJ
                    data = get_cnpj_data(cnpj)
                    cnpj_cache[cnpj] = data
                else:
                    raise e # Re-lança outros erros HTTP
            
            time.sleep(3.0) # Delay para evitar sobrecarga na API
        
        # Atualizar o DataFrame original com os dados do cache
        if cnpj_cache[cnpj]:
            # Encontrar todos os índices no DataFrame original que correspondem a este CNPJ
            indices = df[df['CNPJ_CLEAN'] == cnpj].index
            
            for key, value in cnpj_cache[cnpj].items():
                # Atualizar apenas se o valor for válido (não None ou vazio)
                if value is not None and value != '':
                    df.loc[indices, key] = value
    
    print("Enriquecimento de dados concluído.")
    
    # Remover a coluna CNPJ_CLEAN temporária
    df = df.drop(columns=['CNPJ_CLEAN'])
    
    return df

# --- Script Principal ---

# 1. Carregar os dados
try:
    # Usar o caminho do arquivo diretamente, assumindo que está no mesmo diretório ou o caminho é ajustado
    df = pd.read_excel(FILE_PATH)
    
    # Padronizar nomes das colunas (mantido do código original)
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('Á', 'A').str.replace('Ã', 'A').str.replace('Ç', 'C').str.replace('Ê', 'E').str.replace('Õ', 'O').str.replace('Ú', 'U').str.upper()
    
    # 2. Enriquecer os dados
    df = enrich_data(df)
    
    # 3. Salvar o DataFrame enriquecido em CSV (conforme solicitado)
    output_csv_path = 'vendas_enriquecidas.csv'
    df.to_csv(output_csv_path, index=False)
    print(f"\nDados enriquecidos salvos em: {output_csv_path}")
    
except Exception as e:
    print(f"Erro fatal durante o processamento: {e}")
    exit()

# 4. Preparação dos dados de treinamento (Oportunidades Fechadas)
df_fechadas = df[df['DATA_DA_VENDA'].notna()].copy()
df_fechadas['DATA_DA_VENDA'] = pd.to_datetime(df_fechadas['DATA_DA_VENDA'])
df_fechadas['DATA_CICLO_DE_BUSCA'] = pd.to_datetime(df_fechadas['DATA_CICLO_DE_BUSCA'])
df_fechadas['DIAS_PARA_FECHAMENTO'] = (df_fechadas['DATA_DA_VENDA'] - df_fechadas['DATA_CICLO_DE_BUSCA']).dt.days
df_fechadas = df_fechadas[df_fechadas['DIAS_PARA_FECHAMENTO'] > 0] # Filtrar dias inválidos

# 5. Definição de Features (X) e Target (y)
# Adicionar as novas colunas categóricas
categorical_features = [
    'ORIGEM', 'ETAPA_ATUAL', 'ESN', 'GSN', 'TIPO_DE_ATUACAO',
    'PRODUTO_DA_OPORTUNIDADE', 'PRODUTO_SUGERIDO',
    'CNAE_FISCAL', 'PORTE', 'NATUREZA_JURIDICA', 'SITUACAO_CADASTRAL', 'UF', 'MUNICIPIO'
]
numerical_features = ['VALOR_SUGERIDO']
all_features = categorical_features + numerical_features

# Filtrar o DataFrame para incluir apenas as features que existem (algumas podem ter sido removidas se não existiam)
# Isso é uma medida de segurança, embora o código de enriquecimento garanta que existam.
existing_features = [f for f in all_features if f in df_fechadas.columns]

X = df_fechadas[existing_features]
y = df_fechadas['DIAS_PARA_FECHAMENTO']

# 6. Pré-processamento: One-Hot Encoding para variáveis categóricas
# Atualizar a lista de features categóricas para o preprocessor
categorical_features_for_preprocessor = [f for f in categorical_features if f in existing_features]

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features_for_preprocessor)
    ],
    remainder='passthrough' # Manter colunas numéricas
)

# 7. Criação do Pipeline: Pré-processamento + Modelo
    #Abaixo estão os parâmetros mais importantes para deixar o modelo mais forte:
    #a) n_estimators (quantidade de árvores)
    #   Aumentar → melhora a previsão, mas deixa mais lento. Valor recomendado para testar: 200, 300, 500
    #b) learning_rate (passo de aprendizado)
    #   Muito alto → overfitting
    #   Muito baixo → modelo lento para aprender, mas mais preciso. Recomendado testar: 0.05, 0.02, 0.01
    #c) max_depth (profundidade das árvores)
    #   Controla a capacidade de aprender padrões.
    #   Profundidades menores reduzem overfitting. Testar: 3, 4, 5
    #d) min_samples_split e min_samples_leaf
    #   Controlam o mínimo de dados por divisão/folha.
    #   Ajudam muito contra overfitting.
    #
    # Overfitting é quando o modelo “decorou” os dados de treino em vez de aprender o padrão real. 
    # Ele fica ótimo no treino, mas vai mal em dados novos porque não generaliza.

model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42))
])

# 8. Treinamento do modelo (usando todos os dados disponíveis para um modelo final)
model.fit(X, y)

# 9. Avaliação (apenas para fins de demonstração no console)
y_pred = model.predict(X)
mae = mean_absolute_error(y, y_pred)
r2 = r2_score(y, y_pred)

print(f"\nTreinamento concluído.")
print(f"Métricas de avaliação (no conjunto de treinamento):")
print(f"MAE (Erro Absoluto Médio): {mae:.2f} dias")
print(f"R-quadrado: {r2:.2f}")

# 10. Salvar o modelo treinado e a lista de features
joblib.dump(model, 'modelo_fechamento.pkl')
joblib.dump(existing_features, 'features_list.pkl')

print("\nModelo e artefatos salvos: 'modelo_fechamento.pkl' e 'features_list.pkl'.")

