import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Prompt Ops Hub
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Human-in-loop review and approval for AI-generated code changes
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Review Runs
          </h2>
          <p className="text-gray-600 mb-4">
            Review and approve AI-generated code changes with integrity checks and human oversight.
          </p>
          <Link href="/runs" className="btn-primary inline-block">
            View Runs
          </Link>
        </div>

        <div className="card">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Integrity Dashboard
          </h2>
          <p className="text-gray-600 mb-4">
            Monitor integrity metrics, coverage trends, and violation patterns across all runs.
          </p>
          <Link href="/integrity" className="btn-primary inline-block">
            View Dashboard
          </Link>
        </div>
      </div>

      <div className="card">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          How it works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">1. AI Generation</h3>
            <p className="text-gray-600">
              AI generates code changes based on task descriptions with automatic testing and integrity checks.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">2. Human Review</h3>
            <p className="text-gray-600">
              Runs with low integrity scores require human approval before proceeding to PR creation.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">3. Approval & Merge</h3>
            <p className="text-gray-600">
              Approved changes automatically create pull requests for final review and merge.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 