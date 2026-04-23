import { Link } from 'react-router-dom';
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react';

export function AnalysisListItem({ analysis }) {
  const score = analysis.score || 0;
  const scoreColor = score >= 70 ? 'bg-green-100 text-green-800' : score >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 flex items-center justify-between hover:shadow-md transition">
      <div className="flex-1">
        <h3 className="font-semibold text-gray-800">{analysis.title || 'Untitled'}</h3>
        <p className="text-sm text-gray-600">{analysis.company || 'Company'}</p>
        <div className="flex items-center gap-4 mt-2">
          <div className={`px-3 py-1 rounded text-sm font-medium ${scoreColor}`}>{score}</div>
          {analysis.is_valid ? (
            <div className="flex items-center gap-1 text-green-600 text-sm">
              <CheckCircle size={16} /> Valid
            </div>
          ) : (
            <div className="flex items-center gap-1 text-red-600 text-sm">
              <XCircle size={16} /> Not Suitable
            </div>
          )}
        </div>
      </div>
      <Link
        to={`/dashboard/analysis/${analysis.id}`}
        className="flex items-center gap-2 px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded transition"
      >
        View <ArrowRight size={16} />
      </Link>
    </div>
  );
}
