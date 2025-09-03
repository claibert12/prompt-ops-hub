'use client';

import { useQuery } from '@tanstack/react-query';
import { getIntegrityMetrics, type IntegrityMetrics } from '../api';

function getScoreColor(score: number) {
  if (score >= 80) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  return 'text-red-600';
}

function getScoreBgColor(score: number) {
  if (score >= 80) return 'bg-green-100';
  if (score >= 70) return 'bg-yellow-100';
  return 'bg-red-100';
}

export default function IntegrityPage() {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['integrity-metrics'],
    queryFn: async () => {
      const result = await getIntegrityMetrics();
      if (result.error) throw new Error(result.error);
      return result.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading integrity metrics...</div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="text-center">
        <div className="text-red-600 mb-4">Error loading integrity metrics</div>
        <button
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900">Integrity Dashboard</h1>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Total Runs</h3>
          <p className="text-3xl font-bold text-gray-900">{metrics.total_runs}</p>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Average Integrity Score</h3>
          <p className={`text-3xl font-bold ${getScoreColor(metrics.avg_integrity_score)}`}>
            {metrics.avg_integrity_score.toFixed(1)}/100
          </p>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Weekly Runs</h3>
          <p className="text-3xl font-bold text-gray-900">{metrics.weekly_stats.total_runs}</p>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Weekly Violations</h3>
          <p className="text-3xl font-bold text-red-600">{metrics.weekly_stats.violations_count}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Violations by Type */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Violations by Type</h2>
          {Object.keys(metrics.violations_by_type).length === 0 ? (
            <p className="text-gray-600">No violations recorded</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(metrics.violations_by_type)
                .sort(([, a], [, b]) => b - a)
                .map(([type, count]) => (
                  <div key={type} className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">
                      {type.replace('_', ' ')}
                    </span>
                    <span className="text-sm font-bold text-red-600">{count}</span>
                  </div>
                ))}
            </div>
          )}
        </div>

        {/* Weekly Stats */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Weekly Statistics</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Average Integrity Score</span>
              <span className={`text-sm font-bold ${getScoreColor(metrics.weekly_stats.avg_integrity_score)}`}>
                {metrics.weekly_stats.avg_integrity_score.toFixed(1)}/100
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Total Runs</span>
              <span className="text-sm font-bold text-gray-900">{metrics.weekly_stats.total_runs}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Total Violations</span>
              <span className="text-sm font-bold text-red-600">{metrics.weekly_stats.violations_count}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Coverage Trend */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Integrity Score Trend</h2>
        {metrics.coverage_trend.length === 0 ? (
          <p className="text-gray-600">No trend data available</p>
        ) : (
          <div className="space-y-3">
            {metrics.coverage_trend.map((point, index) => (
              <div key={index} className="flex items-center space-x-4">
                <span className="text-sm text-gray-600 w-24">{point.date}</span>
                <div className="flex-1">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getScoreBgColor(point.score)}`}
                      style={{ width: `${point.score}%` }}
                    ></div>
                  </div>
                </div>
                <span className={`text-sm font-bold ${getScoreColor(point.score)}`}>
                  {point.score}/100
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Integrity Insights */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Integrity Insights</h2>
        <div className="space-y-4">
          {metrics.avg_integrity_score >= 80 ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-lg font-medium text-green-800 mb-2">✅ Excellent Integrity</h3>
              <p className="text-green-700">
                Your average integrity score of {metrics.avg_integrity_score.toFixed(1)}/100 indicates 
                high-quality code generation with minimal violations.
              </p>
            </div>
          ) : metrics.avg_integrity_score >= 70 ? (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="text-lg font-medium text-yellow-800 mb-2">⚠️ Good Integrity</h3>
              <p className="text-yellow-700">
                Your average integrity score of {metrics.avg_integrity_score.toFixed(1)}/100 is acceptable, 
                but there's room for improvement. Consider reviewing common violation types.
              </p>
            </div>
          ) : (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="text-lg font-medium text-red-800 mb-2">❌ Low Integrity</h3>
              <p className="text-red-700">
                Your average integrity score of {metrics.avg_integrity_score.toFixed(1)}/100 indicates 
                significant issues. Review violation patterns and consider adjusting generation parameters.
              </p>
            </div>
          )}

          {Object.keys(metrics.violations_by_type).length > 0 && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-medium text-blue-800 mb-2">📊 Top Violation</h3>
              <p className="text-blue-700">
                Most common violation: <strong>
                  {Object.entries(metrics.violations_by_type)
                    .sort(([, a], [, b]) => b - a)[0][0]
                    .replace('_', ' ')}
                </strong> 
                ({Object.entries(metrics.violations_by_type)
                  .sort(([, a], [, b]) => b - a)[0][1]} occurrences)
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 