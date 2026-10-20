import { defineConfig, devices } from "@playwright/test";


const baseURL =
  process.env.ELASI_E2E_BASE_URL ?? "http://127.0.0.1:3000";
const startLocalFrontend = !process.env.ELASI_E2E_BASE_URL;


export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: "list",
  timeout: 45_000,
  expect: {
    timeout: 8_000,
  },
  use: {
    baseURL,
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        browserName: "chromium",
      },
    },
  ],
  ...(startLocalFrontend
    ? {
        webServer: {
          command: "npm run dev -- --hostname 127.0.0.1",
          url: `${baseURL}/robots.txt`,
          reuseExistingServer: !process.env.CI,
          timeout: 120_000,
        },
      }
    : {}),
});
