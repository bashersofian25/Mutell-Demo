import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";
import "flatpickr/dist/flatpickr.css";

const outfit = Outfit({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Mutell",
  description: "AI-Powered Customer Interaction Platform",
  icons: {
    icon: "/mutell-logo.svg",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${outfit.className} dark:bg-gray-900`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}