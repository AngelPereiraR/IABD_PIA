import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Layout, Spinner } from '../../../shared/components';
import { AdaptationPreview } from '../components/AdaptationPreview';
import { PDFDownloadButton } from '../components/PDFDownloadButton';
import { ResultCard } from '../../analysis/components/ResultCard';
import useStore from '../../../stores/globalStore';
import { analysisService } from '../../../services/analysisService';
import { ArrowLeft, Zap } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function AdaptationPage() {
  const { t } = useLocale();
  const { analysisId } = useParams();
  const [searchParams] = useSearchParams();
  const analysisIdAsNumber = parseInt(analysisId, 10);
  const navigate = useNavigate();
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  const handleBack = () => {
    const fromParam = searchParams.get('from');
    if (analysisId) {
      const backUrl = fromParam
        ? `/dashboard/analysis/${analysisId}?from=${fromParam}`
        : `/dashboard/analysis/${analysisId}`;
      navigate(backUrl);
    } else {
      navigate('/dashboard/analysis');
    }
  };

  const { currentAnalysis, currentAdaptation, isGenerating, setCurrentAnalysis, setCurrentAdaptation, createAdaptation } = useStore((state) => ({
    currentAnalysis: state.analysis.currentAnalysis,
    currentAdaptation: state.adaptations.currentAdaptation,
    isGenerating: state.adaptations.isGenerating,
    setCurrentAnalysis: state.analysisActions.setCurrentAnalysis,
    setCurrentAdaptation: state.adaptationActions.setCurrentAdaptation,
    createAdaptation: state.adaptationActions.createAdaptation,
  }));

  // Load analysis on mount or when analysisId changes
  useEffect(() => {
    const fetchAnalysis = async () => {
      // Clear previous adaptation when loading new analysis
      if (currentAnalysis && currentAnalysis.id !== analysisIdAsNumber) {
        setCurrentAdaptation(null);
      }

      if (currentAnalysis && currentAnalysis.id === analysisIdAsNumber) {
        return;
      }

      setIsLoadingAnalysis(true);
      setAnalysisError(null);
      try {
        const response = await analysisService.getAnalysis(analysisIdAsNumber);
        setCurrentAnalysis(response.data);
      } catch (err) {
        setAnalysisError(err.message);
        setTimeout(() => navigate('/dashboard/analysis/history'), 2000);
      } finally {
        setIsLoadingAnalysis(false);
      }
    };

    fetchAnalysis();
  }, [analysisId, analysisIdAsNumber, currentAnalysis, navigate, setCurrentAnalysis, setCurrentAdaptation]);

  const handleGenerateAdaptation = async () => {
    const result = await createAdaptation(analysisIdAsNumber);
    if (result.success && result.data) {
      navigate(`/dashboard/adaptations/${result.data.id}`);
    }
  };

  const handleRegenerateAdaptation = async () => {
    setCurrentAdaptation(null);
    await createAdaptation(analysisIdAsNumber);
  };

  // Loading analysis
  if (isLoadingAnalysis) {
    return (
      <Layout>
        <Spinner message={t('common.loading')} fullHeight />
      </Layout>
    );
  }

  // Error loading analysis
  if (analysisError) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-400 font-mono">{t('common.error')} {t('analysis.error')} {t('nav.back')}...</p>
        </div>
      </Layout>
    );
  }

  // No analysis loaded
  if (!currentAnalysis) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-brand-white/70 font-mono">{t('common.loading')}</p>
        </div>
      </Layout>
    );
  }

  // Analysis loaded but adaptation being generated
  if (isGenerating && !currentAdaptation) {
    return (
      <Layout>
        <Spinner message={t('adaptations.generating')} fullHeight />
        <p className="text-brand-white/70 text-sm text-center mt-2 font-mono">{t('pages.adaptations.patience')}</p>
      </Layout>
    );
  }

  // Adaptation generated - show preview
  if (currentAdaptation) {
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

          <div className="relative space-y-6">
            {isGenerating && (
              <div className="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center rounded-lg z-10">
                <div className="flex flex-col items-center gap-2">
                  <Spinner size={32} text={t('pages.adaptations.updating')} />
                </div>
              </div>
            )}

            <AdaptationPreview
              adaptation={currentAdaptation}
              isLoading={isGenerating}
            />

            {currentAdaptation && !isGenerating && (
              <div className="flex gap-4">
                <PDFDownloadButton adaptationId={currentAdaptation.id} />
                <button
                  onClick={handleRegenerateAdaptation}
                  disabled={isGenerating}
                  className="flex items-center gap-2 px-6 py-3 bg-brand-gold text-brand-black border-2 border-brand-gold font-mono font-bold hover:bg-brand-white transition disabled:opacity-50"
                >
                  <Zap size={18} /> {t('pages.adaptations.regenerate')}
                </button>
              </div>
            )}
          </div>
        </div>
      </Layout>
    );
  }

  // Analysis loaded - show analysis details and generate button
  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 mb-6"
        >
          <ArrowLeft size={18} /> {t('nav.back')}
        </button>

        <h1 className="text-3xl font-display font-bold text-brand-white mb-8">{t('pages.adaptations.generateAdapted')}</h1>

        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-display font-semibold text-brand-white mb-4">{t('pages.analysis.analyzeJobOffer')}</h2>
            <ResultCard result={currentAnalysis} />
          </div>

          {currentAnalysis.is_valid && (
            <div className="flex gap-4">
              <button
                onClick={handleGenerateAdaptation}
                disabled={isGenerating}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-brand-gold text-brand-black border-2 border-brand-gold font-mono font-bold hover:bg-brand-white transition disabled:opacity-50"
              >
                {isGenerating ? (
                  <>
                    <Spinner size={18} inline color="text-white" /> {t('adaptations.generating')}
                  </>
                ) : (
                  <>
                    <Zap size={18} /> {t('pages.adaptations.generateAdapted')}
                  </>
                )}
              </button>
            </div>
          )}

          {!currentAnalysis.is_valid && (
            <div className="bg-red-950/40 p-4 border-2 border-red-900">
              <p className="text-red-400 font-mono">{t('analysis.notRecommended')} - {t('analysis.minScore')}</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}