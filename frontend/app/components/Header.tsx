import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-primary-700 to-primary-500 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold tracking-tight">
          Prompt Ops Hub
        </Link>
        <nav className="flex items-center space-x-2">
          <Link
            href="/runs"
            className="px-3 py-2 rounded-md text-sm font-medium hover:bg-white/10"
          >
            Runs
          </Link>
          <Link
            href="/integrity"
            className="px-3 py-2 rounded-md text-sm font-medium hover:bg-white/10"
          >
            Integrity
          </Link>
        </nav>
      </div>
    </header>
  );
}
