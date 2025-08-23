/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/health',
        destination: 'http://localhost:8000/health',
      },
      {
        source: '/auth/:path*',
        destination: 'http://localhost:8000/auth/:path*',
      },
      {
        source: '/rooms/:path*',
        destination: 'http://localhost:8000/rooms/:path*',
      },
    ];
  },
};

module.exports = nextConfig;