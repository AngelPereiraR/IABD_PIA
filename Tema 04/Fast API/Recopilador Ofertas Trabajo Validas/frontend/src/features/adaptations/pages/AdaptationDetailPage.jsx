import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Layout, Spinner } from '../../../shared/components';
import { AdaptationPreview } from '../components/AdaptationPreview';
import { PDFDownloadButton } from '../components/PDFDownloadButton';
import useStore from '../../../stores/globalStore';
import { ArrowLeft } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function AdaptationDetailPage() {
  const { t } = useLocale();
  const { adaptationId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fromParam = searchParams.get('from');
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
  }, [adaptationId]);

  const handleBack = () => {
    if (analysisId) {
      const backUrl = fromParam
        ? `/dashboard/analysis/${analysisId}?from=${fromParam}`
        : `/dashboard/analysis/${analysisId}`;
      navigate(backUrl);
    } else {
      navigate('/dashboard/adaptations');
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <Spinner message={t('adaptations.generating')} fullHeight />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-400 font-mono">{error} {t('nav.back')}...</p>
        </div>
      </Layout>
    );
  }

  if (!currentAdaptation) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-brand-white/70 font-mono">{t('common.loading')}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-brand-gold hover:text-brand-white font-mono mb-6 transition"
        >
          <ArrowLeft size={18} /> {t('nav.back')}
        </button>

        <h1 className="text-3xl font-display font-bold text-brand-white mb-8">{t('pages.adaptations.yourAdapted')}</h1>

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
