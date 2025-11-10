import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router, protectedProcedure } from "./_core/trpc";
import { z } from "zod";
import { saveOpportunities, getUserOpportunities, clearUserOpportunities } from "./db";
import { parseOpportunitiesFromExcel, predictOpportunitiesClosure } from "./ml";

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  // Procedimentos para previsão de vendas
  sales: router({
    /**
     * Upload de planilha Excel e processamento de previsões
     */
    uploadAndPredict: protectedProcedure
      .input(
        z.object({
          fileData: z.string(), // Base64 encoded file data
          fileName: z.string(),
        })
      )
      .mutation(async ({ ctx, input }) => {
        try {
          // Converter base64 para Buffer
          const buffer = Buffer.from(input.fileData, 'base64');

          // Parsear oportunidades do Excel
          const opportunities = await parseOpportunitiesFromExcel(buffer);

          // Gerar previsões usando o modelo de IA
          const predictedOpportunities = await predictOpportunitiesClosure(opportunities);

          // Limpar oportunidades antigas do usuário
          await clearUserOpportunities(ctx.user.id);

          // Salvar novas oportunidades com previsões no banco de dados
          await saveOpportunities(ctx.user.id, predictedOpportunities);

          return {
            success: true,
            count: predictedOpportunities.length,
            opportunities: predictedOpportunities,
          };
        } catch (error) {
          console.error("Error in uploadAndPredict:", error);
          throw new Error(`Failed to process file: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }),

    /**
     * Obter todas as oportunidades do usuário com previsões
     */
    getOpportunities: protectedProcedure.query(async ({ ctx }) => {
      try {
        const opportunities = await getUserOpportunities(ctx.user.id);
        return opportunities;
      } catch (error) {
        console.error("Error in getOpportunities:", error);
        throw new Error("Failed to fetch opportunities");
      }
    }),

    /**
     * Obter resumo de oportunidades por mês (próximos 12 meses)
     */
    getMonthlySummary: protectedProcedure.query(async ({ ctx }) => {
      try {
        const opportunities = await getUserOpportunities(ctx.user.id);

        // Agrupar por mês da data estimada de fechamento
        const monthlySummary: Record<string, number> = {};

        opportunities.forEach(opp => {
          if (opp.estimatedCloseDate && opp.suggestedValue) {
            const date = new Date(opp.estimatedCloseDate);
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

            if (!monthlySummary[monthKey]) {
              monthlySummary[monthKey] = 0;
            }

            monthlySummary[monthKey] += parseFloat(opp.suggestedValue.toString());
          }
        });

        // Converter para array e ordenar por mês
        const summary = Object.entries(monthlySummary)
          .map(([month, value]) => ({
            month,
            value: Math.round(value * 100) / 100, // Arredondar para 2 casas decimais
          }))
          .sort((a, b) => a.month.localeCompare(b.month));

        return summary;
      } catch (error) {
        console.error("Error in getMonthlySummary:", error);
        throw new Error("Failed to fetch monthly summary");
      }
    }),
  }),
});

export type AppRouter = typeof appRouter;
