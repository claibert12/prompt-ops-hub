import './globals.css';
import { Inter } from 'next/font/google';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Header from './components/Header';
import Footer from './components/Footer';

const inter = Inter({ subsets: ['latin'] });
const queryClient = new QueryClient();

export const metadata = {
  title: 'Prompt Ops Hub - Approval Console',
  description: 'Human-in-loop review and approval for AI-generated code changes',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          <div className="min-h-screen flex flex-col bg-gray-50">
            <Header />
            <main className="flex-1 w-full max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
              {children}
            </main>
            <Footer />
          </div>
        </QueryClientProvider>
      </body>
    </html>
  );
}