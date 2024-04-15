import type { Metadata } from "next";
import { Inter } from "next/font/google";
import ProfilePopup from './profiles'; // Adjust the import path as needed
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BluebookAI",
  description: "BluebookAI Assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ProfilePopup /> {/* This renders the profile popup across all pages using this layout */}
        {children}
      </body>
    </html>
  );
}