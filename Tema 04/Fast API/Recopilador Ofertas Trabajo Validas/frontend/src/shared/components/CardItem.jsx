import { Link } from 'react-router-dom';
import { Calendar, TrendingUp, CheckCircle, XCircle } from 'lucide-react';

export function CardItem({
  linkPath,
  icon: Icon,
  title,
  company,
  score,
  createdAt,
  isValid,
  badgeColor = 'bg-indigo-100 text-indigo-700',
  searchParams = {},
}) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-600 bg-green-50';
    if (score >= 50) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const searchParamsString = Object.keys(searchParams).length > 0
    ? '?' + new URLSearchParams(searchParams).toString()
    : '';

  return (
    <Link
      to={linkPath + searchParamsString}
      className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-indigo-400 hover:shadow-md transition"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <Icon size={20} className="flex-shrink-0 mt-1" />
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-800 truncate">{title}</h3>
            <p className="text-sm text-gray-600 truncate">{company}</p>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Calendar size={14} />
                {formatDate(createdAt)}
              </div>
              {isValid !== undefined && (
                <div className="flex items-center gap-1">
                  {isValid ? (
                    <>
                      <CheckCircle size={14} className="text-green-600" />
                      <span className="text-xs text-green-700 font-medium">Valid</span>
                    </>
                  ) : (
                    <>
                      <XCircle size={14} className="text-red-600" />
                      <span className="text-xs text-red-700 font-medium">Not Suitable</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          {score !== null && score !== undefined && (
            <div className={`flex items-center gap-1 px-3 py-1 rounded font-semibold ${getScoreColor(score)}`}>
              <TrendingUp size={16} />
              {score}
            </div>
          )}
          <div className={`inline-block px-3 py-1 rounded text-sm font-medium ${badgeColor}`}>
            View
          </div>
        </div>
      </div>
    </Link>
  );
}
