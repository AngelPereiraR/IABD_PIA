import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Layout, Spinner } from '../../../shared/components';
import { ResultCard } from '../components/ResultCard';
import { CardItem } from '../../../shared/components/CardItem';
import useStore from '../../../stores/globalStore';
import { analysisService } from '../../../services/analysisService';
import { adaptationService } from '../../../services/adaptationService';
import { ArrowLeft, Zap, FileText } from 'lucide-react';

export function ResultPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const idAsNumber = parseInt(id, 10);
  const navigate = useNavigate();
  const fromParam = searchParams.get('from') || 'analysis';
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [adaptations, setAdaptations] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const { currentAnalysis, setCurrentAnalysis, createAdaptation } = useStore((state) => ({
    currentAnalysis: state.analysis.currentAnalysis,
    setCurrentAnalysis: state.analysisActions.setCurrentAnalysis,
    createAdaptation: state.adaptationActions.createAdaptation,
  }));

  const handleBack = () => {
    if (fromParam === 'history') {
      navigate('/dashboard/analysis/history');
    } else {
      navigate('/dashboard/analysis');
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // If analysis is in store and matches the ID, skip fetching it
        let analysisData = currentAnalysis && currentAnalysis.id === idAsNumber
          ? currentAnalysis
          : null;

        // Load analysis and adaptations in parallel
        const [analysisResponse, adaptationsResponse] = await Promise.all([
          analysisData ? Promise.resolve(null) : analysisService.getAnalysis(idAsNumber),
          adaptationService.getAdaptationHistory(100, 0),
        ]);

        // Set analysis if it was fetched
        if (analysisResponse) {
          setCurrentAnalysis(analysisResponse.data);
          analysisData = analysisResponse.data;
        }

        // Filter and set adaptations for this offer
        const offerAdaptations = (adaptationsResponse.data.items || []).filter(
          (a) => a.job_offer_id === idAsNumber
        );
        setAdaptations(offerAdaptations);
      } catch (err) {
        setError(err.message);
        // Redirect to history if analysis not found
        setTimeout(() => navigate('/dashboard/analysis/history'), 2000);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [id, idAsNumber, currentAnalysis, navigate, setCurrentAnalysis]);

  const handleGenerateAdaptation = async () => {
    setIsGenerating(true);
    const result = await createAdaptation(idAsNumber);
    setIsGenerating(false);
    if (result.success && result.data) {
      setAdaptations([result.data, ...adaptations]);
      navigate(`/dashboard/adaptations/${result.data.id}?from=analysis&analysisId=${idAsNumber}`);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <Spinner message="Loading analysis..." fullHeight />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto text-center py-12">
          <p className="text-red-600 mb-4">Error loading analysis. Redirecting...</p>
        </div>
      </Layout>
    );
  }

  if (!currentAnalysis) {
    return (
      <Layout>
        <Spinner message="Loading..." fullHeight />
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

        <ResultCard result={currentAnalysis} />

        {currentAnalysis.is_valid ? (
          <button
            onClick={handleGenerateAdaptation}
            disabled={isGenerating}
            className="inline-flex items-center justify-center gap-2 mt-6 px-6 py-3 w-full bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-gray-400 transition"
          >
            {isGenerating ? (
              <>
                <Spinner size={18} inline color="text-white" /> Generating...
              </>
            ) : (
              <>
                <Zap size={18} /> Generate CV Adaptation
              </>
            )}
          </button>
        ) : (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">This offer does not meet the minimum match score (60%). Cannot generate adaptation.</p>
          </div>
        )}

        {adaptations.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Generated Adaptations</h2>
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
                  searchParams={{ from: 'analysis', analysisId: currentAnalysis.id }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
