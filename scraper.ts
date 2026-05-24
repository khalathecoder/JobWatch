import { invokeLLM } from "../_core/llm";
import { notifyOwner } from "../_core/notification";
// Database operations will be implemented when drizzle is properly configured

export interface JobMatch {
  title: string;
  company: string;
  location: string;
  url: string;
  description: string;
  postedDate?: Date;
}

/**
 * Daily scraper service that:
 * 1. Fetches jobs from approved companies
 * 2. Compares with existing jobs to find new ones
 * 3. Marks expired jobs as closed
 * 4. Scores jobs against user profile
 * 5. Triggers notifications for new relevant jobs
 */
export class ScraperService {
  private db: any = null;

  async initialize() {
    // TODO: Initialize database connection when drizzle is properly configured
    if (!this.db) {
      console.warn("[Scraper] Database not initialized");
    }
  }

  /**
   * Run daily scrape for all approved companies
   */
  async runDailyScrape(userId: number) {
    try {
      await this.initialize();

      // Get all approved companies for this user
      const approvedCompanies: any[] = [];
      // TODO: Implement database query when drizzle is properly configured

      let totalNewJobs = 0;
      let totalExpiredJobs = 0;

      for (const company of approvedCompanies) {
        const { newJobs, expiredJobs } = await this.scrapeCompany(
          userId,
          company
        );
        totalNewJobs += newJobs;
        totalExpiredJobs += expiredJobs;
      }

      // TODO: Log the scan to database
      console.log(
        `[Scraper] Daily scrape completed: ${totalNewJobs} new jobs, ${totalExpiredJobs} expired`
      );

      return {
        success: true,
        newJobs: totalNewJobs,
        expiredJobs: totalExpiredJobs,
      };
    } catch (error) {
      console.error("[Scraper] Daily scrape failed:", error);
      throw error;
    }
  }

  /**
   * Scrape a single company and handle job comparison
   */
  private async scrapeCompany(userId: number, company: any) {
    try {
      // Fetch current jobs from company career page
      const currentJobs = await this.fetchJobsFromCompany(company);

      // Get existing jobs for this company
      const existingJobs: any[] = [];
      // TODO: Implement database query when drizzle is properly configured

      // Find new jobs (not in existing list)
      const existingUrls = new Set(existingJobs.map((j) => j.url));
      const newJobs = currentJobs.filter((j) => !existingUrls.has(j.url));

      // Find expired jobs (in existing list but not in current list)
      const currentUrls = new Set(currentJobs.map((j) => j.url));
      const expiredJobs = existingJobs.filter(
        (j) => !currentUrls.has(j.url)
      );

      // Insert new jobs
      for (const job of newJobs) {
        const score = await this.scoreJob(userId, job);
        // TODO: Insert job into database when drizzle is properly configured

        // If score is high enough, send notification
        if (score >= 70) {
          await this.sendJobAlert(userId, job, score);
        }
      }

      // Mark expired jobs as closed
      // TODO: Update expired jobs in database when drizzle is properly configured

      return {
        newJobs: newJobs.length,
        expiredJobs: expiredJobs.length,
      };
    } catch (error) {
      console.error(
        `[Scraper] Failed to scrape company ${company.name}:`,
        error
      );
      return { newJobs: 0, expiredJobs: 0 };
    }
  }

  /**
   * Fetch jobs from company career page (placeholder - implement with actual scraping)
   */
  private async fetchJobsFromCompany(company: any): Promise<JobMatch[]> {
    // TODO: Implement actual web scraping based on ATS type
    // For now, return empty array
    // In production, this would:
    // 1. Check company.atsType (workday, greenhouse, lever, etc.)
    // 2. Fetch jobs from their career page
    // 3. Parse and extract job details
    return [];
  }

  /**
   * Score a job against user profile using LLM
   */
  private async scoreJob(userId: number, job: JobMatch): Promise<number> {
    try {
      // Get user profile
      const profile = {
        skills: "Security analysis, SIEM, compliance",
        experience: "Product Support Engineer at Solventum",
        preferredRoles: "Security Analyst, Detection Engineer",
        targetIndustries: "Healthcare, Finance, Technology",
      };

      // Use LLM to score the job
      try {
        const response = await invokeLLM({
          messages: [
            {
              role: "system",
              content: `You are a job matching expert. Score how well this job matches the candidate's profile on a scale of 0-100.
              
Candidate Profile:
- Skills: ${profile.skills}
- Experience: ${profile.experience}
- Preferred Roles: ${profile.preferredRoles}
- Target Industries: ${profile.targetIndustries}

Return ONLY a number between 0-100.`,
            },
            {
              role: "user",
              content: `Job Title: ${job.title}\nCompany: ${job.company}\nLocation: ${job.location}\nDescription: ${job.description}`,
            },
          ],
        });

        const content = response.choices[0]?.message?.content;
        const scoreText = typeof content === "string" ? content : "50";
        const score = parseInt(scoreText, 10);
        return isNaN(score) ? 50 : Math.min(100, Math.max(0, score));
      } catch (error) {
        console.error("[Scraper] LLM scoring error:", error);
        return 50;
      }
    } catch (error) {
      console.error("[Scraper] Job scoring failed:", error);
      return 50; // Default score on error
    }
  }

  /**
   * Send job alert via email and in-app notification
   */
  private async sendJobAlert(userId: number, job: JobMatch, score: number) {
    try {
      // Create in-app notification
      // TODO: Implement database insert when drizzle is properly configured
      console.log(
        `[Scraper] New job notification: ${job.title} at ${job.company} (${score}% match)`
      );

      // Send email notification
      try {
        await notifyOwner({
          title: `New Job Alert: ${job.title} at ${job.company}`,
          content: `A new job has been found that matches your profile!\n\nJob: ${job.title}\nCompany: ${job.company}\nLocation: ${job.location}\nMatch Score: ${score}%\n\nView in JobWatch: https://jobwatch.manus.space/dashboard`,
        });
      } catch (error) {
        console.error("[Scraper] Failed to send notification:", error);
      }
    } catch (error) {
      console.error("[Scraper] Failed to send job alert:", error);
    }
  }
}

export const scraperService = new ScraperService();
