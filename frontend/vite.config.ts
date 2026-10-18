import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"
import { VitePWA } from "vite-plugin-pwa"

// https://vitejs.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  plugins: [
    tanstackRouter({
      target: "react",
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "prompt",
      injectRegister: false,
      manifest: {
        name: "識詐練習場 ScamGym",
        short_name: "識詐練習場",
        description: "每天練習辨認詐騙，學會保護自己。",
        lang: "zh-Hant-TW",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        scope: "/",
        // :root --background: oklch(0.975 0.014 90)
        theme_color: "#faf7ec",
        background_color: "#faf7ec",
        icons: [
          { src: "/pwa-192.png", sizes: "192x192", type: "image/png" },
          { src: "/pwa-512.png", sizes: "512x512", type: "image/png" },
          {
            src: "/pwa-maskable-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,woff2,svg}"],
        navigateFallback: "index.html",
        navigateFallbackDenylist: [/^\/(api|docs)(\/|$)/],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: false,
        // API（api.<網域>）不設規則：沒有對應規則的請求不經過 service worker，直接上網
        runtimeCaching: [
          {
            urlPattern: ({ url, sameOrigin }) =>
              sameOrigin &&
              url.pathname.startsWith("/assets/") &&
              !/\/api(\/|$)/.test(url.pathname) &&
              /\.(webp|png|svg)$/i.test(url.pathname),
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "images",
              cacheableResponse: { statuses: [200] },
              expiration: {
                maxEntries: 300,
                maxAgeSeconds: 30 * 24 * 60 * 60,
              },
            },
          },
        ],
      },
    }),
  ],
})
