import original from "./playwright.config"

// 與後端寄出的連結及 CORS 使用相同來源；測試伺服器位於獨立容器。
const origin = process.env.FRONTEND_HOST ?? "http://localhost:17173"
const port = new URL(origin).port || "80"

export default {
  ...original,
  retries: 0,
  reporter: [["list"], ["json", { outputFile: "/artifacts/playwright.json" }]],
  outputDir: "/artifacts/playwright-traces",
  use: { ...original.use, baseURL: origin },
  webServer: {
    command: `bun run dev --host 0.0.0.0 --port ${port}`,
    url: origin,
    reuseExistingServer: false,
  },
}
