import { clerkSetup } from "@clerk/testing/playwright";
import { test as setup } from "@playwright/test";

setup.describe.configure({ mode: "serial" });

setup("obtain a Clerk development testing token", async () => {
  await clerkSetup();
});
