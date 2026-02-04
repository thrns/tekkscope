import DocsSidebar from "./components/DocsSidebar";
import DocsTopBar from "./components/DocsTopBar";

export const metadata = {
  title: "Tekkscope Docs",
  description: "API documentation and guides for Tekkscope Search and Research APIs.",
  robots: { index: true, follow: true },
  icons: {
    icon: "/favicon.ico",
  },
  openGraph: {
    type: "website",
    title: "Tekkscope API Docs",
    description: "Explore Tekkscope Search, Lens, DeepLens, ReportLens, and Chat APIs.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tekkscope API Docs",
    description: "Tekkscope Search and Research API documentation",
  },
};

export default function DocsLayout({ children }) {
  return (
    <main className={`flex h-screen w-full bg-tekk-bg `}>
      <aside className="flex w-full overflow-hidden ">
        <DocsSidebar />
        <div className="flex w-full max-w-full flex-col overflow-hidden pb-20 md:pb-0">
          <DocsTopBar />
          <div className="w-full overflow-auto h-screen   px-6 ">
            {children}
          </div>
        </div>
      </aside>
    </main>
  );
}
