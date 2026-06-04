import path from "node:path";
import { defineConfig } from "@playwright/test";

const repoRoot = path.resolve(__dirname, "../..");
const backendDir = path.resolve(repoRoot, "apps/api");

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:3100",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "./scripts/start-e2e-backend.sh",
      cwd: __dirname,
      url: "http://127.0.0.1:8100/api/v1/jobs",
      reuseExistingServer: false,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        ...process.env,
        DJANGO_DB_NAME: path.resolve(backendDir, "e2e.sqlite3"),
      },
    },
    {
      command: "pnpm exec next build && pnpm exec next start --hostname 127.0.0.1 --port 3100",
      cwd: __dirname,
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      stdout: "pipe",
      stderr: "pipe",
      env: {
        ...process.env,
        NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8100/api/v1",
      },
    },
  ],
});
