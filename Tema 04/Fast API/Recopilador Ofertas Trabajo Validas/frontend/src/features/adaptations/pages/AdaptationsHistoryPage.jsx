import { useEffect } from 'react';
import { Layout, Spinner } from '../../../shared/components';
import { CardItem } from '../../../shared/components/CardItem';
import useStore from '../../../stores/globalStore';
import { useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, FileText } from 'lucide-react';

export function AdaptationsHistoryPage() {
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
          <h1 className="text-3xl font-bold text-gray-800 mb-2">My Adaptations</h1>
          {total > 0 && (
            <p className="text-gray-600">
              Total adaptations: <span className="font-semibold text-indigo-600">{total}</span>
            </p>
          )}
        </div>

        {isLoadingHistory ? (
          <Spinner message="Loading adaptations..." />
        ) : adaptations.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600">No adapted CVs yet. Generate one from an analysis.</p>
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
                badgeColor="bg-indigo-100 text-indigo-700"
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
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded disabled:bg-gray-300 disabled:text-gray-600 transition"
            >
              <ChevronLeft size={18} /> Previous
            </button>
            <span className="px-4 py-2 text-gray-700 font-semibold">
              Page {page} of {maxPages}
            </span>
            <button
              onClick={handleNextPage}
              disabled={isLastPage}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded disabled:bg-gray-300 disabled:text-gray-600 transition"
            >
              Next <ChevronRight size={18} />
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
