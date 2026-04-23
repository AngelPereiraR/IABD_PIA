import { useEffect, useState } from 'react';
import { Layout } from '../../../shared/components';
import { AnalysisListItem } from '../components/AnalysisListItem';
import useStore from '../../../stores/globalStore';

export function HistoryPage() {
  const [page, setPage] = useState(0);
  const { analyses, loadAnalysisHistory } = useStore((state) => ({
    analyses: state.analysis.analyses,
    loadAnalysisHistory: state.analysisActions.loadAnalysisHistory,
  }));

  useEffect(() => {
    loadAnalysisHistory(10, page * 10);
  }, [page]);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Analysis History</h1>

        {analyses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">No analyses yet. Start by analyzing a job offer.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {analyses.map((analysis) => (
              <AnalysisListItem key={analysis.id} analysis={analysis} />
            ))}
          </div>
        )}

        {analyses.length > 0 && (
          <div className="flex gap-2 justify-center mt-8">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-4 py-2 text-gray-700">Page {page + 1}</span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={analyses.length < 10}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
