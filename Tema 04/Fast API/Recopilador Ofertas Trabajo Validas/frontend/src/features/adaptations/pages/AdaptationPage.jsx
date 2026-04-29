import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Layout, Spinner } from '../../../shared/components';
import { AdaptationPreview } from '../components/AdaptationPreview';
import { PDFDownloadButton } from '../components/PDFDownloadButton';
import { ResultCard } from '../../analysis/components/ResultCard';
import useStore from '../../../stores/globalStore';
import { analysisService } from '../../../services/analysisService';
import { ArrowLeft, Zap } from 'lucide-react';

export function AdaptationPage() {
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
        <Spinner message="Loading analysis..." fullHeight />
      </Layout>
    );
  }

  // Error loading analysis
  if (analysisError) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-red-600">Error loading analysis. Redirecting...</p>
        </div>
      </Layout>
    );
  }

  // No analysis loaded
  if (!currentAnalysis) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </Layout>
    );
  }

  // Analysis loaded but adaptation being generated
  if (isGenerating && !currentAdaptation) {
    return (
      <Layout>
        <Spinner message="Generating your adapted CV..." fullHeight />
        <p className="text-gray-500 text-sm text-center mt-2">This may take a moment</p>
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
            className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 mb-6"
          >
            <ArrowLeft size={18} /> Back
          </button>

          <h1 className="text-3xl font-bold text-gray-800 mb-8">Your Adapted CV</h1>

          <div className="relative space-y-6">
            {isGenerating && (
              <div className="absolute inset-0 bg-white/50 backdrop-blur-sm flex items-center justify-center rounded-lg z-10">
                <div className="flex flex-col items-center gap-2">
                  <Spinner size={32} text="Updating..." />
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
                  className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-gray-400 transition"
                >
                  <Zap size={18} /> Regenerate
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
          <ArrowLeft size={18} /> Back
        </button>

        <h1 className="text-3xl font-bold text-gray-800 mb-8">Generate Adapted CV</h1>

        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Job Analysis</h2>
            <ResultCard result={currentAnalysis} />
          </div>

          {currentAnalysis.is_valid && (
            <div className="flex gap-4">
              <button
                onClick={handleGenerateAdaptation}
                disabled={isGenerating}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-gray-400 transition"
              >
                {isGenerating ? (
                  <>
                    <Spinner size={18} inline color="text-white" /> Generating...
                  </>
                ) : (
                  <>
                    <Zap size={18} /> Generate Adapted CV
                  </>
                )}
              </button>
            </div>
          )}

          {!currentAnalysis.is_valid && (
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <p className="text-red-700">This offer does not meet the minimum match score (60%). Cannot generate adaptation.</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}