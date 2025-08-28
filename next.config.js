/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable image optimization for non-image media files
  images: {
    unoptimized: true,
  },
  // Handle API and media routes
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
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