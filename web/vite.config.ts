import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"]
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
    sourcemap: true
  }
});
