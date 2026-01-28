import type { Metadata } from "next";
import Navbar from "./components/Navbar";

export const metadata: Metadata = {
  metadataBase: new URL("https://tekkscope.com"),
  title: "Tekkscope - Automate Your Workflow",
  description:
    "Tekkscope helps you automate your workflow and increase productivity.",
  keywords: ["tekkscope", "automation", "workflow", "productivity", "saas"],
  icons: "/favicon.ico",
  openGraph: {
    title: "Tekkscope - Automate Your Workflow",
    description:
      "Tekkscope helps you automate your workflow and increase productivity.",
    url: "https://tekkscope.com",
    siteName: "Tekkscope",
    images: [
      {
        url: "/logos/logo-flat.png",
        width: 1200,
        height: 630,
        alt: "Tekkscope Logo",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tekkscope - Automate Your Workflow",
    description:
      "Tekkscope helps you automate your workflow and increase productivity.",
    creator: "@tekkscope",
    images: ["/logos/logo-flat.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://tekkscope.com",
    languages: {
      "en-US": "https://tekkscope.com/en-US",
    },
  },
  assets: ["https://tekkscope.com/assets"],
  category: "technology",
};

export default function LandingPageLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Tekkscope",
    url: "https://tekkscope.com",
    logo: "https://tekkscope.com/logos/logo-flat.png",
    contactPoint: {
      "@type": "ContactPoint",
      telephone: "+1-555-555-5555",
      contactType: "customer service",
    },
    sameAs: ["https://twitter.com/tekkscope"],
  };

  return (
    <main className={`flex min-h-screen w-full `}>
      <aside className="flex w-full flex-col items-start">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <Navbar />
        {children}
      </aside>
    </main>
  );
}
