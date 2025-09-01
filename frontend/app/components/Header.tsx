import Link from 'next/link';

export default function Header() {
  return (
    <header className="bg-white border-b shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="text-xl font-semibold text-gray-900">
          Prompt Ops Hub
        </Link>
        <nav className="flex items-center space-x-4">
          <Link
            href="/runs"
            className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
          >
            Runs
          </Link>
          <Link
            href="/integrity"
            className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
          >
            Integrity
          </Link>
        </nav>
      </div>
    </header>
  );
}
