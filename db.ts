import { drizzle } from "drizzle-orm/mysql2";
import mysql from "mysql2/promise";
import { eq, and, desc, gte } from "drizzle-orm";
import type { User, InsertUser } from "../drizzle/schema";
import * as schema from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

/**
 * Get or create the database connection
 */
async function getDb() {
  if (!_db && ENV.databaseUrl) {
    try {
      const connection = await mysql.createConnection(ENV.databaseUrl);
      _db = drizzle(connection, { schema });
    } catch (error) {
      console.error("[Database] Failed to connect:", error);
      throw error;
    }
  }
  return _db;
}

/**
 * User operations
 */
export async function getUserByOpenId(openId: string): Promise<User | undefined> {
  const db = await getDb();
  if (!db) return undefined;

  try {
    const result = await db
      .select()
      .from(schema.users)
      .where(eq(schema.users.openId, openId))
      .limit(1);

    return result[0];
  } catch (error) {
    console.error("[Database] Error getting user by openId:", error);
    return undefined;
  }
}

export async function upsertUser(data: Partial<Omit<InsertUser, "id">>): Promise<void> {
  const db = await getDb();
  if (!db) return;

  try {
    if (!data.openId) {
      throw new Error("User openId is required for upsert");
    }

    await db
      .insert(schema.users)
      .values(data as any)
      .onDuplicateKeyUpdate({
        set: data as any,
      });
  } catch (error) {
    console.error("[Database] Error upserting user:", error);
    throw error;
  }
}

/**
 * Profile operations
 */
export async function getUserProfile(userId: number) {
  const db = await getDb();
  if (!db) return null;

  try {
    const result = await db
      .select()
      .from(schema.userProfiles)
      .where(eq(schema.userProfiles.userId, userId))
      .limit(1);

    return result[0] || null;
  } catch (error) {
    console.error("[Database] Error getting user profile:", error);
    return null;
  }
}

export async function upsertUserProfile(userId: number, data: any) {
  const db = await getDb();
  if (!db) return;

  try {
    const existing = await db
      .select()
      .from(schema.userProfiles)
      .where(eq(schema.userProfiles.userId, userId))
      .limit(1);

    if (existing.length > 0) {
      await db
        .update(schema.userProfiles)
        .set({ ...data, updatedAt: new Date() })
        .where(eq(schema.userProfiles.userId, userId));
    } else {
      await db.insert(schema.userProfiles).values({
        userId,
        ...data,
      });
    }
  } catch (error) {
    console.error("[Database] Error upserting user profile:", error);
    throw error;
  }
}

/**
 * Job operations
 */
export async function getJobs(userId: number, filters?: any) {
  const db = await getDb();
  if (!db) return [];

  try {
    const result = await db
      .select()
      .from(schema.jobs)
      .where(eq(schema.jobs.userId, userId))
      .orderBy(desc(schema.jobs.foundAt));

    return result;
  } catch (error) {
    console.error("[Database] Error getting jobs:", error);
    return [];
  }
}

export async function createJob(userId: number, data: any) {
  const db = await getDb();
  if (!db) return null;

  try {
    const result = await db.insert(schema.jobs).values({
      userId,
      ...data,
      foundAt: new Date(),
    });

    return result;
  } catch (error) {
    console.error("[Database] Error creating job:", error);
    throw error;
  }
}

export async function updateJob(jobId: number, data: any) {
  const db = await getDb();
  if (!db) return;

  try {
    await db
      .update(schema.jobs)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(schema.jobs.id, jobId));
  } catch (error) {
    console.error("[Database] Error updating job:", error);
    throw error;
  }
}

/**
 * Company operations
 */
export async function getCompanies(userId: number) {
  const db = await getDb();
  if (!db) return [];

  try {
    const result = await db
      .select()
      .from(schema.companies)
      .where(eq(schema.companies.userId, userId));

    return result;
  } catch (error) {
    console.error("[Database] Error getting companies:", error);
    return [];
  }
}

export async function createCompany(userId: number, data: any) {
  const db = await getDb();
  if (!db) return null;

  try {
    const result = await db.insert(schema.companies).values({
      userId,
      ...data,
    });

    return result;
  } catch (error) {
    console.error("[Database] Error creating company:", error);
    throw error;
  }
}

export async function updateCompany(companyId: number, data: any) {
  const db = await getDb();
  if (!db) return;

  try {
    await db
      .update(schema.companies)
      .set({ ...data, updatedAt: new Date() })
      .where(eq(schema.companies.id, companyId));
  } catch (error) {
    console.error("[Database] Error updating company:", error);
    throw error;
  }
}

/**
 * Scan Log operations
 */
export async function createScanLog(userId: number, data: any) {
  const db = await getDb();
  if (!db) return null;

  try {
    const result = await db.insert(schema.scanLogs).values({
      userId,
      ...data,
    });

    return result;
  } catch (error) {
    console.error("[Database] Error creating scan log:", error);
    throw error;
  }
}

export async function getScanLogs(userId: number) {
  const db = await getDb();
  if (!db) return [];

  try {
    const result = await db
      .select()
      .from(schema.scanLogs)
      .where(eq(schema.scanLogs.userId, userId))
      .orderBy(desc(schema.scanLogs.startedAt));

    return result;
  } catch (error) {
    console.error("[Database] Error getting scan logs:", error);
    return [];
  }
}
