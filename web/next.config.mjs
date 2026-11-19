/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // 127.0.0.1, not localhost: on Windows `localhost` resolves to ::1 first and
    // the Docker port is IPv4, which turned every proxied call into a 500.
    const apiOrigin = process.env.API_ORIGIN || "http://127.0.0.1:7860";
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/:path*`,
      },
    ];
  },
};

export default nextConfig;
