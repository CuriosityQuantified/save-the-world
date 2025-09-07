/** @type {import('next').NextConfig} */
const { getBackendPortSync } = require('./utils/backendPort');

// Get the backend port synchronously for configuration
const backendPort = getBackendPortSync();
console.log(`Next.js config: Backend detected on port ${backendPort}`);

const nextConfig = {
  reactStrictMode: true,
  // Disable image optimization for non-image media files
  images: {
    unoptimized: true,
  },
  // Handle API and media routes
  async rewrites() {
    // Re-check port in case it changed
    const currentPort = getBackendPortSync();
    return [
      {
        source: '/api/:path*',
        destination: `http://localhost:${currentPort}/:path*`,
      },
      {
        source: '/media/:path*',
        destination: '/media/:path*',
      },
    ];
  },
  // Redirect root to /simulation
  async redirects() {
    return [
      {
        source: '/',
        destination: '/simulation',
        permanent: false,
      },
    ];
  },
}

module.exports = nextConfig; 