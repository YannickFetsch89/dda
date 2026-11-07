// Tests für die Website (npm test). Nur Logik und Server-Komponenten, kein Browser.
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./", import.meta.url)),
      // Next.js bringt „server-only“ intern mit; in Tests (Node) ist es ein leeres Modul
      "server-only": fileURLToPath(new URL("./tests/leer.ts", import.meta.url)),
    },
  },
  test: { environment: "node", include: ["tests/**/*.test.{ts,tsx}"] },
});
