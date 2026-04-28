import { CheckCircle, XCircle, DollarSign, Briefcase, Building2, AlertCircle, ThumbsUp, Brain, ExternalLink, Zap } from 'lucide-react';

export function ResultCard({ result }) {
  const score = result.score || 0;
  const scoreColor = score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600';
  const bgColor = score >= 70 ? 'bg-green-50' : score >= 50 ? 'bg-yellow-50' : 'bg-red-50';

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
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

      {(result.summary || result.benefits || (result.key_skills && result.key_skills.length > 0)) && (
        <div className={`p-4 rounded-lg border-2 space-y-4 ${bgColor} ${score >= 70 ? 'border-green-200' : score >= 50 ? 'border-yellow-200' : 'border-red-200'}`}>
          <div className="flex items-start gap-3">
            <Brain size={20} className={`flex-shrink-0 mt-0.5 ${score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'}`} />
            <div className="flex-1">
              <p className="font-semibold text-gray-800 mb-2">AI Analysis Summary</p>
              {result.summary && (
                <p className="text-gray-700 leading-relaxed mb-4">{result.summary}</p>
              )}

              {result.benefits && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Benefits</p>
                  <p className="text-gray-700 text-sm">{result.benefits}</p>
                </div>
              )}

              {result.key_skills && result.key_skills.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Required Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {result.key_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-white bg-opacity-50 text-gray-700 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {result.salary && (
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <DollarSign size={20} className="text-indigo-600 flex-shrink-0" />
          <div>
            <p className="text-sm text-gray-600">Salary</p>
            <p className="font-semibold text-gray-800">{result.salary}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {result.job_type && (
          <div className="flex items-center gap-2">
            <Briefcase size={18} className="text-indigo-600 flex-shrink-0" />
            <div>
              <p className="text-sm text-gray-600">Type</p>
              <p className="font-medium text-gray-800">{result.job_type}</p>
            </div>
          </div>
        )}
        {result.location && (
          <div className="flex items-center gap-2">
            <Building2 size={18} className="text-indigo-600 flex-shrink-0" />
            <div>
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-medium text-gray-800">{result.location}</p>
            </div>
          </div>
        )}
      </div>

      {result.offer_url && (
        <div className="pt-4 border-t border-gray-200">
          <a
            href={result.offer_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded font-medium transition"
          >
            <ExternalLink size={16} />
            View Original Offer
          </a>
        </div>
      )}
    </div>
  );
}
