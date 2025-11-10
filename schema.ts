import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, decimal } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Tabela para armazenar oportunidades de vendas com previsões
 */
export const opportunities = mysqlTable("opportunities", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  
  // Dados originais da oportunidade
  opportunityId: varchar("opportunityId", { length: 255 }).notNull(),
  opportunityName: varchar("opportunityName", { length: 255 }).notNull(),
  origin: varchar("origin", { length: 100 }),
  clientName: varchar("clientName", { length: 255 }),
  cnpj: varchar("cnpj", { length: 20 }),
  currentStage: varchar("currentStage", { length: 100 }),
  esn: varchar("esn", { length: 100 }),
  gsn: varchar("gsn", { length: 100 }),
  activityType: varchar("activityType", { length: 100 }),
  closingFeeling: int("closingFeeling"), // Percentual (0-100)
  humanForecastDate: timestamp("humanForecastDate"),
  productOpportunity: varchar("productOpportunity", { length: 255 }),
  suggestedProduct: varchar("suggestedProduct", { length: 255 }),
  suggestedValue: decimal("suggestedValue", { precision: 15, scale: 2 }),
  
  // Dados de previsão da IA
  predictedDaysToClose: int("predictedDaysToClose"),
  estimatedCloseDate: timestamp("estimatedCloseDate"),
  
  // Metadados
  uploadedAt: timestamp("uploadedAt").defaultNow().notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Opportunity = typeof opportunities.$inferSelect;
export type InsertOpportunity = typeof opportunities.$inferInsert;
