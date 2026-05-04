/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // Empty at root for local Docker / `npm run dev`. GitHub Pages sets NEXT_PUBLIC_BASE_PATH=/clearCites in CI.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? "",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
