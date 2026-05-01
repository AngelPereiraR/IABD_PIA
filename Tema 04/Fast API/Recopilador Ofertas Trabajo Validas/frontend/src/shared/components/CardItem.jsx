import { Link } from 'react-router-dom';
import { Calendar, Star, CheckCircle, XCircle } from 'lucide-react';
import { useLocale } from '../../hooks/useLocale';

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
  const { t } = useLocale();

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-500 bg-green-950/40';
    if (score >= 50) return 'text-yellow-500 bg-yellow-950/40';
    return 'text-red-500 bg-red-950/40';
  };

  const searchParamsString = Object.keys(searchParams).length > 0
    ? '?' + new URLSearchParams(searchParams).toString()
    : '';

  return (
    <Link
      to={linkPath + searchParamsString}
      className="block p-4 bg-brand-gray border-2 border-brand-gray-light hover:border-brand-gold transition"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <Icon size={20} className="flex-shrink-0 mt-1 text-brand-gold" />
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-brand-white truncate">{title}</h3>
            <p className="text-sm text-brand-white/70 truncate">{company}</p>
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              <div className="flex items-center gap-1 text-xs text-brand-white/50 font-mono">
                <Calendar size={14} />
                {formatDate(createdAt)}
              </div>
              {isValid !== undefined && (
                <div className="flex items-center gap-1">
                  {isValid ? (
                    <>
                      <CheckCircle size={14} className="text-green-500" />
                      <span className="text-xs text-green-500 font-medium">{t('common.valid')}</span>
                    </>
                  ) : (
                    <>
                      <XCircle size={14} className="text-red-500" />
                      <span className="text-xs text-red-500 font-medium">{t('pages.analysis.notSuitable')}</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          {score !== null && score !== undefined && (
            <div className={`flex items-center gap-1 px-3 py-1 font-semibold font-mono ${getScoreColor(score)}`}>
              <Star size={16} />
              {score}
            </div>
          )}
          <div className="inline-block px-3 py-1 text-sm font-medium bg-brand-gold text-brand-black">
            {t('common.view')}
          </div>
        </div>
      </div>
    </Link>
  );
}
