import { useMemo } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function ChartTab() {
  const { data: monthlySummary, isLoading, error } = trpc.sales.getMonthlySummary.useQuery();

  // Preparar dados para o gráfico (próximos 12 meses)
  const chartData = useMemo(() => {
    if (!monthlySummary) return [];

    // Gerar os próximos 12 meses a partir de hoje
    const today = new Date();
    const months = [];

    for (let i = 0; i < 12; i++) {
      const date = new Date(today.getFullYear(), today.getMonth() + i, 1);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      const monthName = date.toLocaleDateString("pt-BR", { month: "short", year: "numeric" });

      const summary = monthlySummary.find((s) => s.month === monthKey);
      months.push({
        month: monthName,
        monthKey,
        value: summary?.value || 0,
      });
    }

    return months;
  }, [monthlySummary]);

  const totalValue = useMemo(() => {
    return chartData.reduce((sum, item) => sum + item.value, 0);
  }, [chartData]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-muted-foreground" />
            <p className="text-muted-foreground">Carregando dados...</p>
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
          Erro ao carregar dados: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-muted-foreground">
              Nenhum dado disponível. Faça upload de uma planilha para ver as previsões.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Previsão de Receita - Próximos 12 Meses</CardTitle>
          <CardDescription>
            Somatória dos valores sugeridos agrupados por mês da data provável de fechamento
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Chart */}
          <div className="w-full h-96">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis
                  label={{ value: "Valor (R$)", angle: -90, position: "insideLeft" }}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip
                  formatter={(value) => formatCurrency(value as number)}
                  labelFormatter={(label) => `Mês: ${label}`}
                />
                <Legend />
                <Bar
                  dataKey="value"
                  fill="#3b82f6"
                  name="Valor Previsto"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Valor Total Previsto</p>
              <p className="text-2xl font-bold">{formatCurrency(totalValue)}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Mês com Maior Receita</p>
              <p className="text-2xl font-bold">
                {chartData.length > 0
                  ? formatCurrency(Math.max(...chartData.map((d) => d.value)))
                  : "-"}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Média Mensal</p>
              <p className="text-2xl font-bold">
                {formatCurrency(totalValue / chartData.length)}
              </p>
            </div>
          </div>

          {/* Monthly Breakdown Table */}
          <div className="pt-6 border-t">
            <h3 className="font-semibold mb-4">Detalhamento por Mês</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {chartData.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-muted p-4 rounded-lg flex justify-between items-center"
                >
                  <span className="text-sm font-medium">{item.month}</span>
                  <span className="text-lg font-bold text-primary">
                    {formatCurrency(item.value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
