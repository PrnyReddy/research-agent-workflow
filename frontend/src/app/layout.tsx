import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import MuiThemeProvider from "./ThemeProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Multi-Agent AI Platform",
  description: "An AI platform for complex goal-oriented tasks.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {/* Wrap children in client-side ThemeProvider */}
        <MuiThemeProvider>
          {children}
        </MuiThemeProvider>
      </body>
    </html>
  );
}