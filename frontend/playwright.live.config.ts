/** Browser ↔ real Django (testserver) contract acceptance.
 *
 * Only synthetic data in Django's disposable test database. No API mocking,
 * merchant database, SMS provider or payment requests.
 */
import { defineConfig, devices } from "@playwright/test";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const backendDir = resolve(process.cwd(), "../backend");
const python = process.platform === "win32"
  ? join(backendDir, ".venv", "Scripts", "python.exe")
  : join(backendDir, ".venv", "bin", "python");
// Playwright workers reload this config with a different process.pid.
// Reuse the path inherited from the runner so Django and Chromium agree.
const otpFile = process.env.ELASI_E2E_OTP_FILE ||
  join(tmpdir(), `elasi-browser-e2e-otp-${process.pid}.json`);
process.env.ELASI_E2E_OTP_FILE = otpFile;

const djangoOrigin = "http://127.0.0.1:8017";
const frontendOrigin = "http://127.0.0.1:3110";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "checkout-live.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  reporter: "list",
  expect: { timeout: 10_000 },
  use: {
    baseURL: frontendOrigin,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${python}" manage.py testserver apps/catalog/fixtures/browser_e2e.json --addrport 127.0.0.1:8017 --noinput --settings=config.settings.browser_e2e`,
      cwd: backendDir,
      env: {
        ELASI_BROWSER_E2E_TESTING: "1",
        ELASI_E2E_OTP_FILE: otpFile,
      },
      url: `${djangoOrigin}/api/v1/health/`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm run build && npm run start -- --hostname 127.0.0.1 --port 3110",
      env: {
        INTERNAL_API_ORIGIN: djangoOrigin,
        NEXT_PUBLIC_SITE_URL: frontendOrigin,
      },
      url: `${frontendOrigin}/robots.txt`,
      reuseExistingServer: false,
      timeout: 240_000,
    },
  ],
});
