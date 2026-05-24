import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, boolean, decimal, index } from "drizzle-orm/mysql-core";

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
 * User Profile: Stores personal info, address, and login preferences
 */
export const userProfiles = mysqlTable("userProfiles", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  fullName: varchar("fullName", { length: 255 }),
  phone: varchar("phone", { length: 20 }),
  website: varchar("website", { length: 255 }),
  addressStreet: varchar("addressStreet", { length: 255 }),
  addressCity: varchar("addressCity", { length: 100 }),
  addressState: varchar("addressState", { length: 2 }),
  addressZip: varchar("addressZip", { length: 10 }),
  linkedIn: varchar("linkedIn", { length: 255 }),
  github: varchar("github", { length: 255 }),
  prefUsername: varchar("prefUsername", { length: 100 }),
  prefPasswordHint: varchar("prefPasswordHint", { length: 255 }),
  resumeA: text("resumeA"),
  resumeB: text("resumeB"),
  passionStatement: text("passionStatement"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type UserProfile = typeof userProfiles.$inferSelect;
export type InsertUserProfile = typeof userProfiles.$inferInsert;

/**
 * Jobs: Scraped job listings from Workday, Greenhouse, etc.
 */
export const jobs = mysqlTable("jobs", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  company: varchar("company", { length: 255 }).notNull(),
  location: varchar("location", { length: 255 }),
  url: varchar("url", { length: 1024 }).notNull().unique(),
  description: text("description"),
  status: mysqlEnum("status", ["new", "saved", "applied", "rejected", "archived"]).default("new").notNull(),
  keywords: text("keywords"),
  score: decimal("score", { precision: 5, scale: 2 }),
  scoreReason: text("scoreReason"),
  postedOn: timestamp("postedOn"),
  foundAt: timestamp("foundAt").defaultNow().notNull(),
  seen: boolean("seen").default(false).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId_status").on(table.userId, table.status),
  index("idx_company").on(table.company),
]);

export type Job = typeof jobs.$inferSelect;
export type InsertJob = typeof jobs.$inferInsert;

/**
 * Companies: Tracked companies with their ATS info
 */
export const companies = mysqlTable("companies", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  atsType: varchar("atsType", { length: 50 }),
  careersUrl: varchar("careersUrl", { length: 1024 }),
  verified: boolean("verified").default(false).notNull(),
  hasLiveRoles: boolean("hasLiveRoles").default(false).notNull(),
  sampleRoles: text("sampleRoles"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId_name").on(table.userId, table.name),
]);

export type Company = typeof companies.$inferSelect;
export type InsertCompany = typeof companies.$inferInsert;

/**
 * Company Suggestions: Pending company approvals from the Pro Researcher
 */
export const companySuggestions = mysqlTable("companySuggestions", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  atsType: varchar("atsType", { length: 50 }),
  careersUrl: varchar("careersUrl", { length: 1024 }),
  industry: varchar("industry", { length: 100 }),
  hasLiveRoles: boolean("hasLiveRoles").default(false).notNull(),
  sampleRoles: text("sampleRoles"),
  verified: boolean("verified").default(false).notNull(),
  status: mysqlEnum("status", ["pending", "approved", "rejected"]).default("pending").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId_status").on(table.userId, table.status),
]);

export type CompanySuggestion = typeof companySuggestions.$inferSelect;
export type InsertCompanySuggestion = typeof companySuggestions.$inferInsert;

/**
 * Job Queue: Pending job approvals before they go to the main jobs table
 */
export const jobQueue = mysqlTable("jobQueue", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  company: varchar("company", { length: 255 }).notNull(),
  location: varchar("location", { length: 255 }),
  url: varchar("url", { length: 1024 }).notNull(),
  description: text("description"),
  keywords: text("keywords"),
  score: decimal("score", { precision: 5, scale: 2 }),
  scoreReason: text("scoreReason"),
  status: mysqlEnum("status", ["pending", "approved", "rejected"]).default("pending").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId_status").on(table.userId, table.status),
]);

export type JobQueueItem = typeof jobQueue.$inferSelect;
export type InsertJobQueueItem = typeof jobQueue.$inferInsert;

/**
 * Web Saves: Manually saved jobs from the Chrome extension
 */
export const webSaves = mysqlTable("webSaves", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  company: varchar("company", { length: 255 }).notNull(),
  location: varchar("location", { length: 255 }),
  url: varchar("url", { length: 1024 }).notNull(),
  status: mysqlEnum("status", ["pending", "applied", "archived"]).default("pending").notNull(),
  savedAt: timestamp("savedAt").defaultNow().notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId_status").on(table.userId, table.status),
]);

export type WebSave = typeof webSaves.$inferSelect;
export type InsertWebSave = typeof webSaves.$inferInsert;

/**
 * Scan Logs: Track when scrapers run and their results
 */
export const scanLogs = mysqlTable("scanLogs", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  company: varchar("company", { length: 255 }),
  jobsFound: int("jobsFound").default(0).notNull(),
  status: mysqlEnum("status", ["running", "completed", "failed"]).default("running").notNull(),
  error: text("error"),
  startedAt: timestamp("startedAt").defaultNow().notNull(),
  completedAt: timestamp("completedAt"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
}, (table) => [
  index("idx_userId_company").on(table.userId, table.company),
]);

export type ScanLog = typeof scanLogs.$inferSelect;
export type InsertScanLog = typeof scanLogs.$inferInsert;

/**
 * Experience: User's work experience for resume generation
 */
export const experience = mysqlTable("experience", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  jobTitle: varchar("jobTitle", { length: 255 }).notNull(),
  company: varchar("company", { length: 255 }).notNull(),
  startDate: varchar("startDate", { length: 10 }),
  endDate: varchar("endDate", { length: 10 }),
  resumeVersion: mysqlEnum("resumeVersion", ["A", "B", "both"]).default("both").notNull(),
  responsibilities: text("responsibilities"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId").on(table.userId),
]);

export type Experience = typeof experience.$inferSelect;
export type InsertExperience = typeof experience.$inferInsert;

/**
 * Skills: User's technical and professional skills
 */
export const skills = mysqlTable("skills", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  category: varchar("category", { length: 100 }).notNull(),
  items: text("items"),
  resumeVersion: mysqlEnum("resumeVersion", ["A", "B", "both"]).default("both").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId").on(table.userId),
]);

export type Skill = typeof skills.$inferSelect;
export type InsertSkill = typeof skills.$inferInsert;

/**
 * Education: User's educational background
 */
export const education = mysqlTable("education", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  degree: varchar("degree", { length: 255 }).notNull(),
  school: varchar("school", { length: 255 }).notNull(),
  graduationDate: varchar("graduationDate", { length: 10 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId").on(table.userId),
]);

export type Education = typeof education.$inferSelect;
export type InsertEducation = typeof education.$inferInsert;

/**
 * Certifications: User's professional certifications
 */
export const certifications = mysqlTable("certifications", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => [
  index("idx_userId").on(table.userId),
]);

export type Certification = typeof certifications.$inferSelect;
export type InsertCertification = typeof certifications.$inferInsert;
