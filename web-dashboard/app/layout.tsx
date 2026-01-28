import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Navigation } from "@/components/Navigation";
import { Toaster } from "sonner";
import { EnvCheckBanner } from "@/components/EnvCheckBanner";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "UDO Development Platform v3.0",
  description: "Real-time development automation and monitoring dashboard",
  keywords: ["UDO", "development", "automation", "AI", "dashboard"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-background text-foreground antialiased`}>
        <Providers>
          <EnvCheckBanner />
          <div className="min-h-screen flex flex-col">
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 overflow-x-hidden">
              <div className="max-w-full flex h-16 items-center px-4 overflow-x-auto">
                <div className="mr-4 flex shrink-0">
                  <a className="mr-6 flex items-center space-x-2" href="/">
                    <span className="font-bold text-xl whitespace-nowrap">UDO Platform</span>
                  </a>
                </div>
                <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end overflow-x-auto">
                  <Navigation />
                  <LanguageSwitcher />
                </div>
              </div>
            </header>
            <main className="flex-1">
              {children}
            </main>
          </div>
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
