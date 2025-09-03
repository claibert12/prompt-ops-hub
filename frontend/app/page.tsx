import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-600 to-primary-500 px-6 py-24 text-center text-white shadow-lg">
        <div className="mx-auto max-w-2xl">
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">Prompt Ops Hub</h1>
          <p className="mt-6 text-lg leading-8">
            Human-in-the-loop review and approval for AI-generated code changes.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Link
              href="/runs"
              className="bg-white text-primary-600 hover:bg-gray-100 font-medium py-2 px-4 rounded-md"
            >
              View Runs
            </Link>
            <Link href="/integrity" className="text-sm font-semibold leading-6 text-white hover:underline">
              Integrity Dashboard →
            </Link>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-8 md:grid-cols-3">
        <div className="card text-center">
          <div className="text-3xl mb-4">🤖</div>
          <h3 className="text-xl font-semibold mb-2">AI Generation</h3>
          <p className="text-gray-600">
            Generate code patches with automatic tests and policy checks.
          </p>
        </div>
        <div className="card text-center">
          <div className="text-3xl mb-4">👩‍⚖️</div>
          <h3 className="text-xl font-semibold mb-2">Human Review</h3>
          <p className="text-gray-600">
            Low-integrity runs are routed for manual approval and feedback.
          </p>
        </div>
        <div className="card text-center">
          <div className="text-3xl mb-4">🚀</div>
          <h3 className="text-xl font-semibold mb-2">Auto Merge</h3>
          <p className="text-gray-600">
            Approved changes create pull requests ready for merge.
          </p>
        </div>
      </section>
    </div>
  );
}
