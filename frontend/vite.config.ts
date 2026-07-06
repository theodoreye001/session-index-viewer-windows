import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: Vite serves the frontend on :5173 and proxies /api and
// /favicon.svg to the Python backend on :7333. Production: the
// Python server serves the built bundle from frontend/dist.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:7333",
      "/favicon.svg": "http://127.0.0.1:7333",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
