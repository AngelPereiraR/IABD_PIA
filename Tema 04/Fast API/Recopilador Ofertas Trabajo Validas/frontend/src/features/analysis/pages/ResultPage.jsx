import { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Layout } from '../../../shared/components';
import { ResultCard } from '../components/ResultCard';
import useStore from '../../../stores/globalStore';
import { ArrowLeft, Zap } from 'lucide-react';

export function ResultPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentAnalysis, setCurrentAnalysis } = useStore((state) => ({
    currentAnalysis: state.analysis.currentAnalysis,
    setCurrentAnalysis: state.analysisActions.setCurrentAnalysis,
  }));

  useEffect(() => {
    if (!currentAnalysis || currentAnalysis.id !== id) {
      navigate('/dashboard/analysis');
    }
  }, [id, currentAnalysis, navigate]);

  if (!currentAnalysis) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate('/dashboard/analysis')}
          className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 mb-6"
        >
          <ArrowLeft size={18} /> Back to Analysis
        </button>

        <ResultCard result={currentAnalysis} />

        {currentAnalysis.is_valid && (
          <Link
            to={`/dashboard/adaptations/${currentAnalysis.id}`}
            className="flex items-center justify-center gap-2 mt-6 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition"
          >
            <Zap size={18} /> Generate CV Adaptation
          </Link>
        )}
      </div>
    </Layout>
  );
}
