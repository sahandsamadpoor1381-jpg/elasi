import { defineConfig, devices } from "@playwright/test";

/**
 * ELASI — Playwright E2E Configuration
 *
 * Run browser tests against a production build of Next.js.
 * Keep Django running separately on port 8000.
 *
 * Frontend test server: 127.0.0.1:3100
 * Django API server:   127.0.0.1:8000
 */

const localPort = 3100;

const baseURL =
  process.env.ELASI_E2E_BASE_URL ??
  `http://127.0.0.1:${localPort}`;

const startLocalFrontend = !process.env.ELASI_E2E_BASE_URL;

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",

  // Limit parallel execution for local stability.
  fullyParallel: true,
  workers: 2,

  // Prevent accidental test.only commits in CI.
  forbidOnly: Boolean(process.env.CI),

  // Do not hide failures with automatic retries.
  retries: 0,

  reporter: "list",

  timeout: 45_000,

  expect: {
    timeout: 8_000,
  },

  use: {
    baseURL,

    // Preserve debugging evidence for failed tests.
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
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

  // Start Next.js automatically only for local tests.
  ...(startLocalFrontend
    ? {
        webServer: {
          // Build and start the production version.
          command:
            `npm run build && npm run start -- --hostname 127.0.0.1 --port ${localPort}`,

          // Wait for Next.js to become ready.
          url: `${baseURL}/robots.txt`,

          // Never reuse an existing development server.
          reuseExistingServer: false,

          // Allow time for the production build.
          timeout: 240_000,
        },
      }
    : {}),
});