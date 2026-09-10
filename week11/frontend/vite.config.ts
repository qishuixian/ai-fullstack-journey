import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
export default defineConfig(({ mode }) => ({
  base: loadEnv(mode, ".", "VITE_").VITE_BASE_URL || "/",
  plugins: [vue()],
  server: {
    port: 8003,
    strictPort: true,
    proxy: Object.fromEntries(
      ["/chat", "/approve", "/sessions", "/health"].map((path) => [
        path,
        { target: "http://127.0.0.1:8083" },
      ]),
    ),
  },
  build: { outDir: "../backend/static", emptyOutDir: true },
}));
