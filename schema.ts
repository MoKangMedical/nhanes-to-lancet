import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, json, boolean } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 */
export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
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
 * Research projects table - stores user's research proposals
 */
export const projects = mysqlTable("projects", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  title: varchar("title", { length: 500 }).notNull(),
  description: text("description"),
  // Word document file reference
  proposalFileKey: varchar("proposalFileKey", { length: 500 }),
  proposalFileUrl: text("proposalFileUrl"),
  // PICO/PECO parsed results (JSON)
  picoData: json("picoData").$type<{
    population?: string;
    intervention?: string;
    comparison?: string;
    outcome?: string;
    exposure?: string;
  }>(),
  // Project status
  status: mysqlEnum("status", [
    "draft",           // Initial upload
    "parsing",         // Parsing Word document
    "parsed",          // PICO extracted
    "mapping",         // Mapping variables
    "ready",           // Ready for analysis
    "analyzing",       // Running R analysis
    "completed",       // Analysis completed
    "failed"           // Analysis failed
  ]).default("draft").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Project = typeof projects.$inferSelect;
export type InsertProject = typeof projects.$inferInsert;

/**
 * Variable mappings - NHANES variables identified for the project
 */
export const variableMappings = mysqlTable("variable_mappings", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  // Variable category (exposure, outcome, covariate, etc.)
  category: varchar("category", { length: 100 }).notNull(),
  // Variable name in research proposal
  proposalVariable: varchar("proposalVariable", { length: 500 }).notNull(),
  // Mapped NHANES variable code
  nhanesVariable: varchar("nhanesVariable", { length: 200 }),
  // NHANES dataset name
  nhanesDataset: varchar("nhanesDataset", { length: 200 }),
  // NHANES cycle (e.g., "2017-2018")
  nhanesCycle: varchar("nhanesCycle", { length: 50 }),
  // User confirmed mapping
  confirmed: boolean("confirmed").default(false).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type VariableMapping = typeof variableMappings.$inferSelect;
export type InsertVariableMapping = typeof variableMappings.$inferInsert;

/**
 * Analysis tasks - tracks R analysis execution
 */
export const analysisTasks = mysqlTable("analysis_tasks", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  // Analysis type
  analysisType: mysqlEnum("analysisType", [
    "kaplan_meier",
    "cox_regression",
    "fine_gray",
    "baseline_table",
    "forest_plot"
  ]).notNull(),
  // Analysis configuration (JSON)
  config: json("config").$type<{
    timeVariable?: string;
    eventVariable?: string;
    covariates?: string[];
    stratifyBy?: string;
    competingRisk?: string;
    [key: string]: unknown;
  }>(),
  // Task status
  status: mysqlEnum("status", [
    "pending",
    "running",
    "completed",
    "failed"
  ]).default("pending").notNull(),
  // Error message if failed
  errorMessage: text("errorMessage"),
  // Result file references
  resultFileKey: varchar("resultFileKey", { length: 500 }),
  resultFileUrl: text("resultFileUrl"),
  // R script used
  rScriptPath: varchar("rScriptPath", { length: 500 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type AnalysisTask = typeof analysisTasks.$inferSelect;
export type InsertAnalysisTask = typeof analysisTasks.$inferInsert;

/**
 * Files table - stores all uploaded and generated files
 */
export const files = mysqlTable("files", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  userId: int("userId").notNull(),
  // File type
  fileType: mysqlEnum("fileType", [
    "proposal",           // Uploaded Word proposal
    "nhanes_data",        // Uploaded NHANES data
    "baseline_table",     // Generated baseline table
    "survival_curve",     // Generated survival curve
    "forest_plot",        // Generated forest plot
    "cumulative_incidence", // Generated cumulative incidence curve
    "paper",              // Generated paper document
    "analysis_report",    // Complete analysis report ZIP
    "r_script"            // R analysis script
  ]).notNull(),
  fileName: varchar("fileName", { length: 500 }).notNull(),
  fileKey: varchar("fileKey", { length: 500 }).notNull(),
  fileUrl: text("fileUrl").notNull(),
  mimeType: varchar("mimeType", { length: 200 }),
  fileSize: int("fileSize"), // in bytes
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type File = typeof files.$inferSelect;
export type InsertFile = typeof files.$inferInsert;

/**
 * Generated papers table - stores LLM-generated academic papers
 */
export const papers = mysqlTable("papers", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  userId: int("userId").notNull(),
  // Paper sections
  title: text("title"),
  abstract: text("abstract"),
  introduction: text("introduction"),
  methods: text("methods"),
  results: text("results"),
  discussion: text("discussion"),
  conclusion: text("conclusion"),
  references: json("references").$type<Array<{
    pmid?: string;
    title: string;
    authors: string;
    journal: string;
    year: string;
    doi?: string;
  }>>(),
  // Full paper content (Markdown)
  fullContent: text("fullContent"),
  // Paper file reference
  paperFileKey: varchar("paperFileKey", { length: 500 }),
  paperFileUrl: text("paperFileUrl"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Paper = typeof papers.$inferSelect;
export type InsertPaper = typeof papers.$inferInsert;
