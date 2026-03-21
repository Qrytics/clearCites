import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ScholarGraph – clearCites",
  description:
    "Mapping the DNA of Human Knowledge – a research paper visualization engine.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#0f0f1a", color: "#e2e8f0" }}>
        {children}
      </body>
    </html>
  );
}
