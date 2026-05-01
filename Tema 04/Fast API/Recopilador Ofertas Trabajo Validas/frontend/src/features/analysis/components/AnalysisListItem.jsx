import { Link } from 'react-router-dom';
import { CheckCircle, XCircle, ArrowRight, Target } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function AnalysisListItem({ analysis }) {
  const { t } = useLocale();
  const score = analysis.score || 0;
  const scoreColor = score >= 70 ? 'text-green-500 bg-green-950/40' : score >= 50 ? 'text-yellow-500 bg-yellow-950/40' : 'text-red-500 bg-red-950/40';

  return (
    <div className="bg-brand-gray p-4 border-2 border-brand-gray-light flex items-center justify-between hover:border-brand-gold transition">
      <div className="flex-1">
        <h3 className="font-semibold text-brand-white">{analysis.title || t('pages.analysis.untitled')}</h3>
        <p className="text-sm text-brand-white/70">{analysis.company || t('pages.analysis.company')}</p>
        <div className="flex items-center gap-4 mt-2">
          <div className={`flex items-center gap-1 px-3 py-1 text-sm font-medium font-mono ${scoreColor}`}>
            <Target size={16} /> {score}
          </div>
          {analysis.is_valid ? (
            <div className="flex items-center gap-1 text-green-500 text-sm font-mono">
              <CheckCircle size={16} /> {t('common.valid')}
            </div>
          ) : (
            <div className="flex items-center gap-1 text-red-500 text-sm font-mono">
              <XCircle size={16} /> {t('pages.analysis.notSuitable')}
            </div>
          )}
        </div>
      </div>
      <Link
        to={`/dashboard/analysis/${analysis.id}?from=history`}
        className="flex items-center gap-2 px-4 py-2 border border-transparent text-brand-gold hover:border-brand-gold transition font-mono"
      >
        {t('common.view')} <ArrowRight size={16} />
      </Link>
    </div>
  );
}
