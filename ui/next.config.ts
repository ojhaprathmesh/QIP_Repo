import type { NextConfig } from "next";
import path from "node:path";

// Ensure build succeeds even in offline/sandboxed environments where fonts cannot be downloaded
if (!process.env.NEXT_FONT_GOOGLE_MOCKED_RESPONSES) {
  process.env.NEXT_FONT_GOOGLE_MOCKED_RESPONSES = path.resolve(__dirname, "mock-google-fonts.json");
}

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl.replace(/\/$/, "")}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
