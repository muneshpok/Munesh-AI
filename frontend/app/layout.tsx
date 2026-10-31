import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Munesh AI Dashboard",
  description: "AI-powered WhatsApp business automation platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <h1 className="text-xl font-bold text-primary-700">
                    Munesh AI
                  </h1>
                  <span className="ml-3 text-sm text-gray-500">
                    WhatsApp Business Automation
                  </span>
                </div>
                <div className="flex items-center space-x-4">
                  <a
                    href="/"
                    className="text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Dashboard
                  </a>
                  <a
                    href="/leads"
                    className="text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Leads
                  </a>
                  <a
                    href="/messages"
                    className="text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Messages
                  </a>
                  <a
                    href="/analytics"
                    className="text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Analytics
                  </a>
                  <a
                    href="/self-improvement"
                    className="text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Self-Improvement
                  </a>
                  <a
                    href="/performance"
                    className="text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Performance
                  </a>
                  <a
                    href="/campaigns"
                    className="text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Campaigns
                  </a>
                  <a
                    href="/pricing"
                    className="text-white bg-indigo-600 hover:bg-indigo-700 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Pricing
                  </a>
                </div>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
