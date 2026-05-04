// Fonts and global CSS are set up in app/layout.tsx (root). This wrapper exists for any
// future Discover-only metadata or providers.
export default function DiscoverLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
