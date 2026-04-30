import { useEffect } from 'react';
import { Layout, Spinner } from '../../../shared/components';
import { CardItem } from '../../../shared/components/CardItem';
import useStore from '../../../stores/globalStore';
import { useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function AdaptationsHistoryPage() {
  const { t } = useLocale();
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get('page') || '1', 10);
  const { adaptations, isLoadingHistory, total, loadAdaptationHistory } = useStore((state) => ({
    adaptations: state.adaptations.adaptations,
    isLoadingHistory: state.adaptations.isLoadingHistory,
    total: state.adaptations.total,
    loadAdaptationHistory: state.adaptationActions.loadAdaptationHistory,
  }));

  const itemsPerPage = 10;
  const maxPages = Math.ceil(total / itemsPerPage);
  const isLastPage = page >= maxPages;

  const handlePreviousPage = () => {
    if (page > 1) {
      setSearchParams({ page: page - 1 });
    }
  };

  const handleNextPage = () => {
    if (!isLastPage) {
      setSearchParams({ page: page + 1 });
    }
  };

  useEffect(() => {
    const loadPage = async () => {
      await loadAdaptationHistory(itemsPerPage, (page - 1) * itemsPerPage);
    };
    loadPage();
  }, [page, loadAdaptationHistory]);


  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-display font-bold text-brand-white mb-2">{t('pages.adaptations.myAdaptations')}</h1>
          {total > 0 && (
            <p className="text-brand-white/70 font-mono">
              {t('adaptations.title')}: <span className="font-semibold text-brand-gold">{total}</span>
            </p>
          )}
        </div>

        {isLoadingHistory ? (
          <Spinner message={t('common.loading')} />
        ) : adaptations.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-brand-white/70 font-mono">{t('adaptations.noResults')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {adaptations.map((adaptation) => (
              <CardItem
                key={adaptation.id}
                linkPath={`/dashboard/adaptations/${adaptation.id}`}
                icon={FileText}
                title={adaptation.job_title}
                company={adaptation.company}
                score={adaptation.score}
                createdAt={adaptation.created_at}
                badgeColor="bg-purple-900/40 text-purple-400"
                searchParams={{ from: 'adaptations' }}
              />
            ))}
          </div>
        )}

        {total > 0 && (
          <div className="flex gap-2 justify-center mt-8">
            <button
              onClick={handlePreviousPage}
              disabled={page === 1}
              className="flex items-center gap-2 px-4 py-2 bg-brand-gold text-brand-black border-2 border-brand-gold font-mono font-bold disabled:opacity-50 transition"
            >
              <ChevronLeft size={18} /> {t('nav.back')}
            </button>
            <span className="px-4 py-2 text-brand-white/70 font-semibold font-mono">
              {page} {t('common.of')} {maxPages}
            </span>
            <button
              onClick={handleNextPage}
              disabled={isLastPage}
              className="flex items-center gap-2 px-4 py-2 bg-brand-gold text-brand-black border-2 border-brand-gold font-mono font-bold disabled:opacity-50 transition"
            >
              {t('common.next')} <ChevronRight size={18} />
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
