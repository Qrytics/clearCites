/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // Set basePath to the repo name for GitHub Pages deployment.
  // Override via NEXT_PUBLIC_BASE_PATH env variable (e.g. for a custom domain leave it empty).
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? "/clearCites",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
