import { CheckCircle, XCircle, DollarSign, Briefcase, Building2 } from 'lucide-react';

export function ResultCard({ result }) {
  const score = result.score || 0;
  const scoreColor = score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">{result.title || 'N/A'}</h2>
          <p className="text-gray-600">{result.company || 'Company'}</p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-bold ${scoreColor}`}>{score}</div>
          <p className="text-sm text-gray-600">Match Score</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {result.is_valid ? (
          <>
            <CheckCircle size={20} className="text-green-600" />
            <span className="text-green-700 font-medium">Valid Offer</span>
          </>
        ) : (
          <>
            <XCircle size={20} className="text-red-600" />
            <span className="text-red-700 font-medium">Not Suitable</span>
          </>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {result.salary && (
          <div className="flex items-center gap-2">
            <DollarSign size={18} className="text-indigo-600" />
            <div>
              <p className="text-sm text-gray-600">Salary</p>
              <p className="font-medium text-gray-800">{result.salary}</p>
            </div>
          </div>
        )}
        {result.job_type && (
          <div className="flex items-center gap-2">
            <Briefcase size={18} className="text-indigo-600" />
            <div>
              <p className="text-sm text-gray-600">Type</p>
              <p className="font-medium text-gray-800">{result.job_type}</p>
            </div>
          </div>
        )}
        {result.location && (
          <div className="flex items-center gap-2">
            <Building2 size={18} className="text-indigo-600" />
            <div>
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-medium text-gray-800">{result.location}</p>
            </div>
          </div>
        )}
      </div>

      {result.benefits && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Benefits</p>
          <p className="text-gray-700">{result.benefits}</p>
        </div>
      )}
    </div>
  );
}
