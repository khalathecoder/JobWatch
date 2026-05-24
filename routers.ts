import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router, protectedProcedure } from "./_core/trpc";
import { z } from "zod";
import { COOKIE_NAME } from "@shared/const";
import { scraperService } from "./services/scraper";
import { notificationService } from "./services/notifications";

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

  // Profile Router
  profile: router({
    get: protectedProcedure.query(async ({ ctx }) => {
      return {
        id: ctx.user.id,
        fullName: ctx.user.name || "",
        email: ctx.user.email || "",
        phone: "",
        addressStreet: "3765 Grosvenor Rd",
        addressCity: "South Euclid",
        addressState: "OH",
        addressZip: "44118",
        prefUsername: "khalawright5",
        prefPasswordHint: "JobWatch2026!",
        linkedIn: "",
        github: "",
        resumeA: "",
        resumeB: "",
        passionStatement: "",
      };
    }),

    update: protectedProcedure
      .input(z.object({
        fullName: z.string().optional(),
        phone: z.string().optional(),
        addressStreet: z.string().optional(),
        addressCity: z.string().optional(),
        addressState: z.string().optional(),
        addressZip: z.string().optional(),
        linkedIn: z.string().optional(),
        github: z.string().optional(),
        prefUsername: z.string().optional(),
        prefPasswordHint: z.string().optional(),
        resumeA: z.string().optional(),
        resumeB: z.string().optional(),
        passionStatement: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        return { success: true, message: "Profile updated successfully" };
      }),
  }),

  // Jobs Router
  jobs: router({
    list: protectedProcedure
      .input(z.object({
        status: z.string().optional(),
        limit: z.number().default(50),
        offset: z.number().default(0),
      }))
      .query(async ({ ctx, input }) => {
        return {
          jobs: [],
          total: 0,
        };
      }),

    getById: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ ctx, input }) => {
        return null;
      }),

    updateStatus: protectedProcedure
      .input(z.object({
        id: z.number(),
        status: z.enum(["new", "saved", "applied", "rejected", "archived"]),
      }))
      .mutation(async ({ ctx, input }) => {
        return { success: true };
      }),

    markSeen: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        return { success: true };
      }),
  }),

  // Companies Router
  companies: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return [];
    }),

    getPending: protectedProcedure.query(async ({ ctx }) => {
      return [];
    }),

    approve: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        return { success: true };
      }),

    reject: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        return { success: true };
      }),
  }),

  // Web Saves Router (for manually saved jobs)
  webSaves: router({
    list: protectedProcedure
      .input(z.object({
        status: z.string().optional(),
      }))
      .query(async ({ ctx, input }) => {
        return [];
      }),

    save: protectedProcedure
      .input(z.object({
        title: z.string(),
        company: z.string(),
        location: z.string().optional(),
        url: z.string(),
      }))
      .mutation(async ({ ctx, input }) => {
        return { success: true, id: 1 };
      }),

    updateStatus: protectedProcedure
      .input(z.object({
        id: z.number(),
        status: z.enum(["pending", "applied", "archived"]),
      }))
      .mutation(async ({ ctx, input }) => {
        return { success: true };
      }),
  }),

  // Cover Letter Router
  coverLetter: router({
    generate: protectedProcedure
      .input(z.object({
        jobDescription: z.string(),
        resumeVersion: z.enum(["A", "B"]),
      }))
      .mutation(async ({ ctx, input }) => {
        return {
          coverLetter: "Generated cover letter will appear here...",
        };
      }),
  }),

  // Scraper Router
  scraper: router({
    triggerScan: protectedProcedure
      .input(z.object({
        companies: z.array(z.string()).optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        try {
          const result = await scraperService.runDailyScrape(ctx.user.id);
          return result;
        } catch (error) {
          console.error("[API] Scraper trigger failed:", error);
          return { success: false, error: "Scraper failed" };
        }
      }),

    getStatus: protectedProcedure
      .input(z.object({ scanId: z.number() }))
      .query(async ({ ctx, input }) => {
        return {
          status: "completed",
          jobsFound: 0,
          completedAt: new Date(),
        };
      }),

    getRecentScans: protectedProcedure
      .input(z.object({ limit: z.number().default(10) }))
      .query(async ({ ctx, input }) => {
        return [];
      }),
  }),

  // Notifications Router
  notifications: router({
    getUnread: protectedProcedure.query(async ({ ctx }) => {
      try {
        const unread = await notificationService.getUnreadNotifications(ctx.user.id);
        return unread;
      } catch (error) {
        console.error("[API] Failed to get notifications:", error);
        return [];
      }
    }),

    markAsRead: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        try {
          await notificationService.markAsRead(input.id);
          return { success: true };
        } catch (error) {
          console.error("[API] Failed to mark notification as read:", error);
          return { success: false };
        }
      }),

    delete: protectedProcedure
      .input(z.object({ id: z.number() }))
      .mutation(async ({ ctx, input }) => {
        try {
          await notificationService.deleteNotification(input.id);
          return { success: true };
        } catch (error) {
          console.error("[API] Failed to delete notification:", error);
          return { success: false };
        }
      }),
  }),
});

export type AppRouter = typeof appRouter;
