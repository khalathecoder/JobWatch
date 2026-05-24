import { describe, expect, it } from "vitest";
import { ENV } from "./_core/env";

describe("Notification Configuration", () => {
  it("should have NOTIFICATION_EMAIL configured", () => {
    expect(ENV.notificationEmail).toBeDefined();
    expect(ENV.notificationEmail).toBe("callmekhala@gmail.com");
    expect(ENV.notificationEmail).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
  });

  it("should have valid email format", () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    expect(emailRegex.test(ENV.notificationEmail)).toBe(true);
  });
});
