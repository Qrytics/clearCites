/** @type {import('next').NextConfig} */
// `output: "export"` breaks `next dev` global CSS (files parse as JS). Enable only for CI static export.
const staticExport =
  process.env.NEXT_STATIC_EXPORT === "true" ||
  process.env.CLEARCITES_STATIC_EXPORT === "true";

const nextConfig = {
  ...(staticExport ? { output: "export" } : {}),
  // Empty at root for local Docker / `npm run dev`. GitHub Pages sets NEXT_PUBLIC_BASE_PATH in CI.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? "",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
