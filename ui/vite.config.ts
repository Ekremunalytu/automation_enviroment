import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": process.env.API_PROXY_TARGET || "http://localhost:8000",
    },
  },
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("echarts")) return "charts";
          if (
            id.includes("react-router-dom") ||
            id.includes("@tanstack/react-query") ||
            id.includes("/react/") ||
            id.includes("/react-dom/")
          ) {
            return "vendor";
          }
          return undefined;
        },
      },
    },
  },
});
