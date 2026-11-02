/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const apiOrigin = process.env.API_ORIGIN || "http://localhost:7860";
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/:path*`,
      },
    ];
  },
};

export default nextConfig;
