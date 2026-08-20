import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Skillet",
  description: "A self-hosted recipe manager",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
