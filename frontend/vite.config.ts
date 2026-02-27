import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/routes": "http://localhost:8000",
      "/stops": "http://localhost:8000",
      "/vehicles": "http://localhost:8000",
      "/simulation": "http://localhost:8000",
    },
  },
});
