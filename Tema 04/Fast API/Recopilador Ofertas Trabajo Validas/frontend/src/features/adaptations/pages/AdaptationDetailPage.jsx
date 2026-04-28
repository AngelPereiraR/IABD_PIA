import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Layout, Spinner } from '../../../shared/components';
import { AdaptationPreview } from '../components/AdaptationPreview';
import { PDFDownloadButton } from '../components/PDFDownloadButton';
import useStore from '../../../stores/globalStore';
import { ArrowLeft } from 'lucide-react';

export function AdaptationDetailPage() {
  const { adaptationId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fromParam = searchParams.get('from') || 'adaptations';
  const analysisId = searchParams.get('analysisId');

  const { currentAdaptation, loadAdaptation } = useStore((state) => ({
    currentAdaptation: state.adaptations.currentAdaptation,
    loadAdaptation: state.adaptationActions.loadAdaptation,
  }));

  useEffect(() => {
    const fetch = async () => {
      if (currentAdaptation && currentAdaptation.id === adaptationId) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const result = await loadAdaptation(adaptationId);
        if (!result.success) {
          setError('Could not load adaptation');
          setTimeout(() => navigate('/dashboard/adaptations'), 2000);
        }
      } catch (err) {
        setError('Error loading adaptation');
      } finally {
        setIsLoading(false);
      }
    };

    fetch();
  }, [adaptationId, currentAdaptation, loadAdaptation, navigate]);

  const handleBack = () => {
    if (fromParam === 'analysis' && analysisId) {
      navigate(`/dashboard/analysis/${analysisId}`);
    } else {
      navigate('/dashboard/adaptations');
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <Spinner message="Loading adaptation..." fullHeight />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600">{error} Redirecting...</p>
        </div>
      </Layout>
    );
  }

  if (!currentAdaptation) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 mb-6"
        >
          <ArrowLeft size={18} /> Back
        </button>

        <h1 className="text-3xl font-bold text-gray-800 mb-8">Adapted CV</h1>

        <div className="space-y-6">
          <AdaptationPreview
            adaptation={currentAdaptation}
            isLoading={false}
          />

          {currentAdaptation && (
            <div className="flex gap-4">
              <PDFDownloadButton adaptationId={currentAdaptation.id} />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
