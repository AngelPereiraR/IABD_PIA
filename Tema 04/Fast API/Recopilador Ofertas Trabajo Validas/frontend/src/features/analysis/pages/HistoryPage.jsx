import { useEffect } from 'react';
import { Layout, Spinner } from '../../../shared/components';
import { CardItem } from '../../../shared/components/CardItem';
import useStore from '../../../stores/globalStore';
import { useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, BarChart3 } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function HistoryPage() {
  const { t } = useLocale();
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get('page') || '1', 10);
  const { analyses, isLoadingHistory, totalAnalyses, loadAnalysisHistory } = useStore((state) => ({
    analyses: state.analysis.analyses,
    isLoadingHistory: state.analysis.isLoadingHistory,
    totalAnalyses: state.analysis.totalAnalyses,
    loadAnalysisHistory: state.analysisActions.loadAnalysisHistory,
  }));

  const itemsPerPage = 10;
  const maxPages = Math.ceil(totalAnalyses / itemsPerPage);
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
      const result = await loadAnalysisHistory(10, (page - 1) * 10);
      // If this page returned no items and we're not on page 1, redirect to previous
      if (result.success && result.itemsCount === 0 && page > 1) {
        setSearchParams({ page: page - 1 });
      }
    };
    loadPage();
  }, [page, loadAnalysisHistory, setSearchParams]);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-display font-bold text-brand-white mb-2">{t('sidebar.analysisHistory')}</h1>
          {totalAnalyses > 0 && (
            <p className="text-brand-white/70 font-mono">
              {t('analysis.history')}: <span className="font-semibold text-brand-gold">{totalAnalyses}</span>
            </p>
          )}
        </div>

        {isLoadingHistory ? (
          <Spinner message={t('common.loading')} />
        ) : analyses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-brand-white/70 font-mono">{t('analysis.noResults')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {analyses.map((analysis) => (
              <CardItem
                key={analysis.id}
                linkPath={`/dashboard/analysis/${analysis.id}`}
                icon={BarChart3}
                title={analysis.title}
                company={analysis.company}
                score={analysis.score}
                createdAt={analysis.created_at}
                isValid={analysis.is_valid}
                badgeColor="bg-purple-900/40 text-purple-400"
                searchParams={{ from: 'history' }}
              />
            ))}
          </div>
        )}

        {totalAnalyses > 0 && (
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
