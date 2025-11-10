import { useMemo } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function GridTab() {
  const { data: opportunities, isLoading, error } = trpc.sales.getOpportunities.useQuery();

  // Ordenar por data provável de fechamento
  const sortedOpportunities = useMemo(() => {
    if (!opportunities) return [];
    return [...opportunities].sort((a, b) => {
      const dateA = a.estimatedCloseDate ? new Date(a.estimatedCloseDate).getTime() : Infinity;
      const dateB = b.estimatedCloseDate ? new Date(b.estimatedCloseDate).getTime() : Infinity;
      return dateA - dateB;
    });
  }, [opportunities]);

  const formatDate = (date: Date | string | null | undefined) => {
    if (!date) return "-";
    const d = new Date(date);
    return d.toLocaleDateString("pt-BR");
  };

  const formatCurrency = (value: string | number | null | undefined) => {
    if (!value) return "-";
    const num = typeof value === "string" ? parseFloat(value) : value;
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(num);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
            <p className="text-muted-foreground">Carregando oportunidades...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800">
          Erro ao carregar oportunidades: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!opportunities || opportunities.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-muted-foreground">
              Nenhuma oportunidade encontrada. Faça upload de uma planilha para começar.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Oportunidades com Previsões</CardTitle>
        <CardDescription>
          {sortedOpportunities.length} oportunidades ordenadas por data provável de fechamento
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Oportunidade</TableHead>
                <TableHead className="w-[150px]">Cliente</TableHead>
                <TableHead className="w-[120px]">Valor</TableHead>
                <TableHead className="w-[120px]">Dias Previstos</TableHead>
                <TableHead className="w-[130px]">Data Provável</TableHead>
                <TableHead className="w-[100px]">Etapa</TableHead>
                <TableHead className="w-[100px]">Feeling (%)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedOpportunities.map((opp, idx) => (
                <TableRow key={idx} className="hover:bg-muted/50">
                  <TableCell className="font-medium text-sm truncate">
                    {opp.opportunityName}
                  </TableCell>
                  <TableCell className="text-sm">{opp.clientName || "-"}</TableCell>
                  <TableCell className="text-sm font-semibold">
                    {formatCurrency(opp.suggestedValue)}
                  </TableCell>
                  <TableCell className="text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {opp.predictedDaysToClose} dias
                    </span>
                  </TableCell>
                  <TableCell className="text-sm font-semibold">
                    {formatDate(opp.estimatedCloseDate)}
                  </TableCell>
                  <TableCell className="text-sm">{opp.currentStage || "-"}</TableCell>
                  <TableCell className="text-sm">{opp.closingFeeling || "-"}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-8 pt-8 border-t">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Total de Oportunidades</p>
            <p className="text-2xl font-bold">{sortedOpportunities.length}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Valor Total</p>
            <p className="text-2xl font-bold">
              {formatCurrency(
                sortedOpportunities.reduce((sum, opp) => {
                  const val = typeof opp.suggestedValue === "string" 
                    ? parseFloat(opp.suggestedValue) 
                    : (opp.suggestedValue || 0);
                  return sum + val;
                }, 0)
              )}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Dias Médios</p>
            <p className="text-2xl font-bold">
              {Math.round(
                sortedOpportunities.reduce((sum, opp) => sum + (opp.predictedDaysToClose || 0), 0) /
                  sortedOpportunities.length
              )}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-muted-foreground">Próximo Fechamento</p>
            <p className="text-2xl font-bold">
              {sortedOpportunities.length > 0
                ? formatDate(sortedOpportunities[0].estimatedCloseDate)
                : "-"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
