'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { getRunDetail, approveRun, rejectRun, type RunDetail } from '../../api';

function getIntegrityColor(score: number) {
  if (score >= 80) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  return 'text-red-600';
}

function getSeverityColor(severity: string) {
  switch (severity) {
    case 'critical':
      return 'text-red-600';
    case 'error':
      return 'text-orange-600';
    case 'warning':
      return 'text-yellow-600';
    default:
      return 'text-gray-600';
  }
}

export default function RunDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [justification, setJustification] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [regenerate, setRegenerate] = useState(false);

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['run', params.id],
    queryFn: async () => {
      const result = await getRunDetail(params.id);
      if (result.error) throw new Error(result.error);
      return result.data;
    },
  });

  const approveMutation = useMutation({
    mutationFn: async () => {
      const result = await approveRun(params.id, justification);
      if (result.error) throw new Error(result.error);
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
      router.push('/runs');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async () => {
      const result = await rejectRun(params.id, rejectionReason, regenerate);
      if (result.error) throw new Error(result.error);
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
      router.push('/runs');
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading run details...</div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="text-center">
        <div className="text-red-600 mb-4">Error loading run details</div>
        <button
          onClick={() => router.back()}
          className="btn-secondary"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="flex justify-between items-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900">
          Run #{run.id}
        </h1>
        <div className="flex items-center space-x-4">
          <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
            run.status === 'tests_passed' ? 'bg-green-100 text-green-800' :
            run.status === 'awaiting_approval' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {run.status.replace('_', ' ')}
          </span>
          <span className={`text-lg font-semibold ${getIntegrityColor(run.integrity.score)}`}>
            {run.integrity.score}/100
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Information */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Task</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task Description
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                {run.task.task_text}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Generated Prompt
              </label>
              <pre className="text-sm text-gray-900 bg-gray-50 p-3 rounded overflow-auto max-h-40">
                {run.task.built_prompt}
              </pre>
            </div>
          </div>
        </div>

        {/* Integrity Report */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Integrity Report</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Score
              </label>
              <span className={`text-2xl font-bold ${getIntegrityColor(run.integrity.score)}`}>
                {run.integrity.score}/100
              </span>
            </div>
            
            {run.integrity.violations.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Violations ({run.integrity.violations.length})
                </label>
                <div className="space-y-2">
                  {run.integrity.violations.map((violation, index) => (
                    <div key={index} className="text-sm p-2 bg-red-50 border border-red-200 rounded">
                      <div className={`font-medium ${getSeverityColor(violation.severity)}`}>
                        {violation.type.replace('_', ' ')}
                      </div>
                      <div className="text-gray-700">{violation.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {run.integrity.questions.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Questions ({run.integrity.questions.length})
                </label>
                <div className="space-y-2">
                  {run.integrity.questions.map((question, index) => (
                    <div key={index} className="text-sm p-2 bg-blue-50 border border-blue-200 rounded">
                      {question}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Diff Preview */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Diff Preview</h2>
        <pre className="text-sm bg-gray-900 text-gray-100 p-4 rounded overflow-auto max-h-96">
          {run.diff}
        </pre>
      </div>

      {/* Test Results */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Results</h2>
        <div className="flex items-center space-x-4">
          <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
            run.test_summary.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {run.test_summary.passed ? 'Passed' : 'Failed'}
          </span>
          <span className="text-sm text-gray-600">
            Status: {run.test_summary.status}
          </span>
        </div>
      </div>

      {/* Approval Actions */}
      {run.status === 'awaiting_approval' && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Review Actions</h2>
          
          {/* Approve */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Approve</h3>
            <div className="space-y-3">
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                placeholder="Justification for approval (optional)"
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
              />
              <button
                onClick={() => approveMutation.mutate()}
                disabled={approveMutation.isPending}
                className="btn-primary"
              >
                {approveMutation.isPending ? 'Approving...' : 'Approve & Open PR'}
              </button>
            </div>
          </div>

          {/* Reject */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Reject</h3>
            <div className="space-y-3">
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Reason for rejection (required)"
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={3}
                required
              />
              <div className="flex items-center space-x-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={regenerate}
                    onChange={(e) => setRegenerate(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Queue for regeneration</span>
                </label>
              </div>
              <button
                onClick={() => rejectMutation.mutate()}
                disabled={rejectMutation.isPending || !rejectionReason.trim()}
                className="btn-danger"
              >
                {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Logs */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Execution Logs</h2>
        <pre className="text-sm bg-gray-900 text-gray-100 p-4 rounded overflow-auto max-h-96">
          {run.logs || 'No logs available'}
        </pre>
      </div>
    </div>
  );
} 