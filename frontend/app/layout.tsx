import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "./contexts/AuthContext";
import { SidebarProvider } from '@/components/ui/sidebar';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AuthProvider>
          <SidebarProvider>{children}</SidebarProvider>
          <Toaster position="top-center" />
        </AuthProvider>
      </body>
    </html>
  );
}
