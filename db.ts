import { eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, opportunities, Opportunity, InsertOpportunity } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

/**
 * Salvar oportunidades no banco de dados
 */
export async function saveOpportunities(userId: number, opps: Partial<InsertOpportunity>[]): Promise<void> {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot save opportunities: database not available");
    return;
  }

  try {
    // Adicionar userId a cada oportunidade
    const oppWithUserId = opps.map(opp => ({
      ...opp,
      userId,
    })) as InsertOpportunity[];

    await db.insert(opportunities).values(oppWithUserId);
  } catch (error) {
    console.error("[Database] Failed to save opportunities:", error);
    throw error;
  }
}

/**
 * Obter todas as oportunidades de um usuário
 */
export async function getUserOpportunities(userId: number): Promise<Opportunity[]> {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get opportunities: database not available");
    return [];
  }

  try {
    const result = await db.select().from(opportunities).where(eq(opportunities.userId, userId));
    return result;
  } catch (error) {
    console.error("[Database] Failed to get opportunities:", error);
    return [];
  }
}

/**
 * Limpar oportunidades antigas de um usuário (para novo upload)
 */
export async function clearUserOpportunities(userId: number): Promise<void> {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot clear opportunities: database not available");
    return;
  }

  try {
    await db.delete(opportunities).where(eq(opportunities.userId, userId));
  } catch (error) {
    console.error("[Database] Failed to clear opportunities:", error);
    throw error;
  }
}
