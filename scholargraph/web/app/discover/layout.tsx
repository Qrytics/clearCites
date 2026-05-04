import { Courier_Prime, DM_Sans, Fraunces } from "next/font/google";

import "./discover.css";

const fontMono = Courier_Prime({
  subsets: ["latin"],
  weight: ["400", "700"],
  style: ["normal", "italic"],
  variable: "--font-mono",
});

const fontSans = DM_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-sans",
});

const fontSerif = Fraunces({
  subsets: ["latin"],
  weight: ["300", "500", "700"],
  variable: "--font-serif",
});

export default function DiscoverLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`${fontMono.variable} ${fontSans.variable} ${fontSerif.variable}`}>{children}</div>
  );
}
