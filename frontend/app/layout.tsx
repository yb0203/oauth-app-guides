import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeToggle } from "@/components/theme-toggle";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "OAuth app guides · verified setup and approval paths",
  description:
    "Verified guides for creating and getting approval for a provider OAuth app, with evidence for every claim. Generate one live for any app.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem("theme");if(t==="dark"||(!t&&matchMedia("(prefers-color-scheme: dark)").matches))document.documentElement.classList.add("dark")}catch(e){}`,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <TooltipProvider delay={150}>
          <header className="print:hidden border-b bg-background/80 backdrop-blur sticky top-0 z-30">
            <div className="mx-auto flex h-12 max-w-[1200px] items-center justify-between px-4 sm:px-6">
              <Link href="/" className="flex items-center gap-2 rounded-md text-sm font-semibold tracking-tight focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none">
                <span aria-hidden className="inline-block size-2.5 rounded-sm bg-foreground" />
                OAuth app guides
              </Link>
              <div className="flex items-center gap-3">
                <span className="hidden text-xs text-muted-foreground sm:inline">Verified setup paths for provider OAuth apps</span>
                <ThemeToggle />
              </div>
            </div>
          </header>
          <main className="flex-1">{children}</main>
        </TooltipProvider>
      </body>
    </html>
  );
}
