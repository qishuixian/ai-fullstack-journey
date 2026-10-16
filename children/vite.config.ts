import { defineConfig, type Plugin } from "vite";
import vue from "@vitejs/plugin-vue";

// Match the production redirect for the entry URL without a trailing slash.
const entryRedirect: Plugin = {
  name: "children-entry-redirect",
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url?.split("?")[0] === "/children") {
        res.writeHead(302, { Location: req.url.replace("/children", "/children/") });
        res.end();
      } else next();
    });
  },
  configurePreviewServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url?.split("?")[0] === "/children") {
        res.writeHead(302, { Location: req.url.replace("/children", "/children/") });
        res.end();
      } else next();
    });
  },
};

export default defineConfig({
  base: "/children/",
  plugins: [entryRedirect, vue()],
  server: { host: "0.0.0.0", port: 8004, strictPort: true },
  build: { outDir: "dist" },
});
