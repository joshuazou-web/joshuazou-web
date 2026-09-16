import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// `base` is relative so the built console works from a subdirectory on a static
// host as well as from the API's own origin.
export default defineConfig({
  base: "./",
  plugins: [react()],
  build: { outDir: "dist", sourcemap: false },
});
