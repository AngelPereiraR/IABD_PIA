import { CheckCircle, XCircle, DollarSign, Briefcase, Building2, AlertCircle, ThumbsUp, Brain, ExternalLink, Zap } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function ResultCard({ result }) {
  const { t } = useLocale();
  const score = result.score || 0;
  const scoreColor = score >= 70 ? 'text-green-500' : score >= 50 ? 'text-yellow-500' : 'text-red-500';
  const bgColor = score >= 70 ? 'bg-green-950/40' : score >= 50 ? 'bg-yellow-950/40' : 'bg-red-950/40';
  const borderColor = score >= 70 ? 'border-green-800/50' : score >= 50 ? 'border-yellow-800/50' : 'border-red-800/50';

  return (
    <div className="bg-brand-gray p-6 border-2 border-brand-gray-light space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-display font-bold text-brand-white">{result.title || t('common.notAvailable')}</h2>
          <p className="text-brand-white/70 font-mono">{result.company || t('pages.analysis.company')}</p>
        </div>
        <div className="text-right">
          <div className={`text-4xl font-display font-bold ${scoreColor}`}>{score}</div>
          <p className="text-sm text-brand-white/70 font-mono">{t('pages.analysis.matchScore')}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {result.is_valid ? (
          <>
            <CheckCircle size={20} className="text-green-500" />
            <span className="text-green-500 font-medium font-mono">{t('pages.analysis.validOffer')}</span>
          </>
        ) : (
          <>
            <XCircle size={20} className="text-red-500" />
            <span className="text-red-500 font-medium font-mono">{t('pages.analysis.notSuitable')}</span>
          </>
        )}
      </div>

      {(result.summary || result.benefits || (result.key_skills && result.key_skills.length > 0)) && (
        <div className={`p-4 border-2 space-y-4 ${bgColor} ${borderColor}`}>
          <div className="flex items-start gap-3">
            <Brain size={20} className={`flex-shrink-0 mt-0.5 ${scoreColor}`} />
            <div className="flex-1">
              <p className="font-display font-bold text-brand-white mb-2">{t('pages.analysis.summary')}</p>
              {result.summary && (
                <p className="text-brand-white/70 leading-relaxed mb-4 font-mono text-sm">{result.summary}</p>
              )}

              {result.benefits && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-brand-white/70 mb-2 font-mono">{t('pages.analysis.benefits')}</p>
                  <p className="text-brand-white/70 text-sm font-mono">{result.benefits}</p>
                </div>
              )}

              {result.key_skills && result.key_skills.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-brand-white/70 mb-2 font-mono">{t('pages.analysis.requiredSkills')}</p>
                  <div className="flex flex-wrap gap-2">
                    {result.key_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-brand-gold/20 text-brand-gold text-sm font-medium font-mono"
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
        <div className="flex items-center gap-2 p-3 bg-brand-gray-light border-2 border-brand-gray-light">
          <DollarSign size={20} className="text-brand-gold flex-shrink-0" />
          <div>
            <p className="text-sm text-brand-white/70 font-mono">{t('pages.analysis.salary')}</p>
            <p className="font-semibold text-brand-white font-mono">
              {result.salary.split(/([€$£¥₹₽¢₩₪₨₦₱₡₵])/).map((part, idx) =>
                /[€$£¥₹₽¢₩₪₨₦₱₡₵]/.test(part) ? (
                  <span key={idx} className="font-sans">{part}</span>
                ) : (
                  <span key={idx}>{part}</span>
                )
              )}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {result.job_type && (
          <div className="flex items-center gap-2">
            <Briefcase size={18} className="text-brand-gold flex-shrink-0" />
            <div>
              <p className="text-sm text-brand-white/70 font-mono">{t('pages.analysis.type')}</p>
              <p className="font-medium text-brand-white font-mono">{result.job_type}</p>
            </div>
          </div>
        )}
        {result.location && (
          <div className="flex items-center gap-2">
            <Building2 size={18} className="text-brand-gold flex-shrink-0" />
            <div>
              <p className="text-sm text-brand-white/70 font-mono">{t('pages.analysis.location')}</p>
              <p className="font-medium text-brand-white font-mono">{result.location}</p>
            </div>
          </div>
        )}
      </div>

      {result.offer_url && (
        <div className="pt-4 border-t-2 border-brand-gray-light">
          <a
            href={result.offer_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 text-brand-gold hover:border-b-2 hover:border-brand-gold font-medium transition font-mono"
          >
            <ExternalLink size={16} />
            {t('pages.analysis.viewOriginal')}
          </a>
        </div>
      )}
    </div>
  );
}
