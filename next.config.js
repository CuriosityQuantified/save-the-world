/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Disable image optimization for non-image media files
  images: {
    unoptimized: true,
  },
  // Handle media files in the public directory
  async rewrites() {
    return [
      {
        source: '/media/:path*',
        destination: '/media/:path*',
      },
    ];
  },
}

module.exports = nextConfig; 