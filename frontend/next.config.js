/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Remove 'standalone' output - Vercel handles deployment
  // output: 'standalone',  // Only needed for Docker deployments
}

module.exports = nextConfig

