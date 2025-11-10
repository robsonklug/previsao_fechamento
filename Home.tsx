import { useState } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import UploadTab from "./UploadTab";
import GridTab from "./GridTab";
import ChartTab from "./ChartTab";
import { APP_LOGO, APP_TITLE } from "@/const";

export default function Home() {
  const { user, loading, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState("upload");
  const [refreshKey, setRefreshKey] = useState(0);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Carregando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted">
        <div className="text-center space-y-6 max-w-md">
          <div className="flex justify-center">
            {APP_LOGO && <img src={APP_LOGO} alt={APP_TITLE} className="h-16 w-16" />}
          </div>
          <div>
            <h1 className="text-3xl font-bold">{APP_TITLE}</h1>
            <p className="text-muted-foreground mt-2">
              Previsão inteligente de fechamento de oportunidades de vendas
            </p>
          </div>
          <p className="text-sm text-muted-foreground">
            Faça login para acessar a aplicação
          </p>
        </div>
      </div>
    );
  }

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
    setActiveTab("grid");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {APP_LOGO && <img src={APP_LOGO} alt={APP_TITLE} className="h-8 w-8" />}
            <h1 className="text-xl font-bold">{APP_TITLE}</h1>
          </div>
          <div className="text-sm text-muted-foreground">
            Bem-vindo, {user?.name || "Usuário"}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="grid">Oportunidades</TabsTrigger>
            <TabsTrigger value="chart">Previsão de Receita</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <UploadTab onUploadSuccess={handleUploadSuccess} />
          </TabsContent>

          <TabsContent value="grid" className="space-y-4">
            <GridTab key={refreshKey} />
          </TabsContent>

          <TabsContent value="chart" className="space-y-4">
            <ChartTab key={refreshKey} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
