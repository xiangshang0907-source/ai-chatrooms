/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove rewrites since nginx will handle API routing
  // Keep headers for direct API calls during development
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET, POST, PUT, DELETE, OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ];
  },
  
  // Development settings
  experimental: {
    serverComponentsExternalPackages: [],
  },
  
  // Output settings for production
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
};

module.exports = nextConfig;