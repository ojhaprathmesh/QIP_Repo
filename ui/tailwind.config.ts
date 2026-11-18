import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyan: "#00f5ff",
        violet: "#a855f7",
        emerald: "#10b981",
        coral: "#f43f5e",
        obsidian: "#090a0f",
      },
    },
  },
  plugins: [],
};

export default config;
