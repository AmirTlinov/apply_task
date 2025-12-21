import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async ({ command }) => ({
  plugins: [react()],
  base: command === "build" && process.env.TAURI_ENV_PLATFORM ? "./" : "/",

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // Vite options tailored for Tauri development
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 5174,
        }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },

  build: {
    modulePreload: {
      polyfill: false,
    },
    // Tauri uses Chromium on Windows and WebKit on macOS and Linux
    target: process.env.TAURI_ENV_PLATFORM === "windows" ? "chrome105" : "safari13",
    // NOTE: WebKit (Linux/macOS) has been observed to crash while evaluating the esbuild-minified React chunk.
    // Keep Windows (Chromium) minified; ship unminified on WebKit for correctness.
    minify:
      process.env.TAURI_ENV_PLATFORM === "windows" && !process.env.TAURI_ENV_DEBUG
        ? "esbuild"
        : false,
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) return;
          if (id.includes("/node_modules/react-dom/") || id.includes("/node_modules/react/")) return "react";
          if (id.includes("/node_modules/scheduler/")) return "react";
          if (id.includes("/node_modules/use-sync-external-store/")) return "react";
          if (id.includes("@tanstack")) return "tanstack";
          if (id.includes("@radix-ui")) return "radix";
          if (id.includes("lucide-react")) return "icons";
          return "vendor";
        },
      },
    },
  },

  envPrefix: ["VITE_", "TAURI_ENV_*"],
}));
