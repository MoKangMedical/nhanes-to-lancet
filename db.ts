import { eq, desc } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { 
  InsertUser, users,
  projects, InsertProject, Project,
  variableMappings, InsertVariableMapping, VariableMapping,
  analysisTasks, InsertAnalysisTask, AnalysisTask,
  files, InsertFile, File,
  papers, InsertPaper, Paper
} from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

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

// Project queries
export async function createProject(project: InsertProject): Promise<Project> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(projects).values(project);
  const insertedId = Number(result[0].insertId);
  
  const inserted = await db.select().from(projects).where(eq(projects.id, insertedId)).limit(1);
  if (!inserted[0]) throw new Error("Failed to retrieve inserted project");
  
  return inserted[0];
}

export async function getProjectById(id: number): Promise<Project | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(projects).where(eq(projects.id, id)).limit(1);
  return result[0];
}

export async function getProjectsByUserId(userId: number): Promise<Project[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(projects).where(eq(projects.userId, userId)).orderBy(desc(projects.createdAt));
}

export async function updateProject(id: number, updates: Partial<InsertProject>): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db.update(projects).set(updates).where(eq(projects.id, id));
}

// Variable mapping queries
export async function createVariableMapping(mapping: InsertVariableMapping): Promise<VariableMapping> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(variableMappings).values(mapping);
  const insertedId = Number(result[0].insertId);
  
  const inserted = await db.select().from(variableMappings).where(eq(variableMappings.id, insertedId)).limit(1);
  if (!inserted[0]) throw new Error("Failed to retrieve inserted mapping");
  
  return inserted[0];
}

export async function getVariableMappingsByProjectId(projectId: number): Promise<VariableMapping[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(variableMappings).where(eq(variableMappings.projectId, projectId));
}

export async function updateVariableMapping(id: number, updates: Partial<InsertVariableMapping>): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db.update(variableMappings).set(updates).where(eq(variableMappings.id, id));
}

// Analysis task queries
export async function createAnalysisTask(task: InsertAnalysisTask): Promise<AnalysisTask> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(analysisTasks).values(task);
  const insertedId = Number(result[0].insertId);
  
  const inserted = await db.select().from(analysisTasks).where(eq(analysisTasks.id, insertedId)).limit(1);
  if (!inserted[0]) throw new Error("Failed to retrieve inserted task");
  
  return inserted[0];
}

export async function getAnalysisTasksByProjectId(projectId: number): Promise<AnalysisTask[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(analysisTasks).where(eq(analysisTasks.projectId, projectId));
}

export async function updateAnalysisTask(id: number, updates: Partial<InsertAnalysisTask>): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db.update(analysisTasks).set(updates).where(eq(analysisTasks.id, id));
}

// File queries
export async function createFile(file: InsertFile): Promise<File> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(files).values(file);
  const insertedId = Number(result[0].insertId);
  
  const inserted = await db.select().from(files).where(eq(files.id, insertedId)).limit(1);
  if (!inserted[0]) throw new Error("Failed to retrieve inserted file");
  
  return inserted[0];
}

export async function getFilesByProjectId(projectId: number): Promise<File[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(files).where(eq(files.projectId, projectId)).orderBy(desc(files.createdAt));
}

// Paper queries
export async function createPaper(paper: InsertPaper): Promise<Paper> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(papers).values(paper);
  const insertedId = Number(result[0].insertId);
  
  const inserted = await db.select().from(papers).where(eq(papers.id, insertedId)).limit(1);
  if (!inserted[0]) throw new Error("Failed to retrieve inserted paper");
  
  return inserted[0];
}

export async function getPaperByProjectId(projectId: number): Promise<Paper | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(papers).where(eq(papers.projectId, projectId)).limit(1);
  return result[0];
}

export async function updatePaper(id: number, updates: Partial<InsertPaper>): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db.update(papers).set(updates).where(eq(papers.id, id));
}
