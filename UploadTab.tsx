import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

interface UploadTabProps {
  onUploadSuccess: () => void;
}

export default function UploadTab({ onUploadSuccess }: UploadTabProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  const uploadMutation = trpc.sales.uploadAndPredict.useMutation({
    onSuccess: (data) => {
      setUploadStatus({
        type: "success",
        message: `Upload realizado com sucesso! ${data.count} oportunidades processadas.`,
      });
      setFile(null);
      setTimeout(() => {
        onUploadSuccess();
      }, 1000);
    },
    onError: (error) => {
      setUploadStatus({
        type: "error",
        message: `Erro ao processar arquivo: ${error.message}`,
      });
    },
  });

  const handleFileSelect = (selectedFile: File) => {
    if (selectedFile.type !== "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" &&
        selectedFile.type !== "application/vnd.ms-excel") {
      setUploadStatus({
        type: "error",
        message: "Por favor, selecione um arquivo Excel (.xlsx ou .xls)",
      });
      return;
    }

    setFile(selectedFile);
    setUploadStatus({ type: null, message: "" });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const arrayBuffer = e.target?.result as ArrayBuffer;
      const base64 = Buffer.from(arrayBuffer).toString("base64");

      uploadMutation.mutate({
        fileData: base64,
        fileName: file.name,
      });
    };
    reader.readAsArrayBuffer(file);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload de Planilha</CardTitle>
          <CardDescription>
            Carregue sua planilha Excel com as oportunidades de vendas para gerar previsões
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Drag and Drop Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragging
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50"
            }`}
          >
            <div className="flex flex-col items-center gap-4">
              <Upload className="h-12 w-12 text-muted-foreground" />
              <div>
                <p className="font-semibold">Arraste sua planilha aqui</p>
                <p className="text-sm text-muted-foreground">ou clique para selecionar</p>
              </div>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
                className="hidden"
                id="file-input"
              />
              <label htmlFor="file-input" className="cursor-pointer">
                <Button type="button" variant="outline">
                  Selecionar Arquivo
                </Button>
              </label>
            </div>
          </div>

          {/* Selected File */}
          {file && (
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm font-medium">Arquivo selecionado:</p>
              <p className="text-sm text-muted-foreground mt-1">{file.name}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Tamanho: {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
          )}

          {/* Status Messages */}
          {uploadStatus.type === "success" && (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                {uploadStatus.message}
              </AlertDescription>
            </Alert>
          )}

          {uploadStatus.type === "error" && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {uploadStatus.message}
              </AlertDescription>
            </Alert>
          )}

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!file || uploadMutation.isPending}
            className="w-full"
            size="lg"
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processando...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Enviar e Processar
              </>
            )}
          </Button>

          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
            <p className="text-sm font-semibold text-blue-900">Instruções:</p>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>A planilha deve conter as colunas: ID, NOME DA OPORTUNIDADE, VALOR SUGERIDO, etc.</li>
              <li>O modelo de IA analisará o histórico de fechamentos para fazer previsões</li>
              <li>As previsões serão exibidas na aba "Oportunidades"</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
