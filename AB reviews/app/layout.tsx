import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AB Reviews",
  description: "Brooke and Archer's invite-only restaurant leaderboard."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
