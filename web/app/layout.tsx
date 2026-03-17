import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuralBrief – Beauty & Wellness Digest",
  description: "Subscribe to our curated newsletter on beauty, wellness, and lifestyle.",
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
