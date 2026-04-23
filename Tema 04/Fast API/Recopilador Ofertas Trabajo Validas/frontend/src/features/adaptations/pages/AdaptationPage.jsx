import { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Layout } from '../../../shared/components';
import { CVPreviewHTML } from '../components/CVPreviewHTML';
import { PDFDownloadButton } from '../components/PDFDownloadButton';
import useStore from '../../../stores/globalStore';
import { ArrowLeft } from 'lucide-react';

export function AdaptationPage() {
  const { analysisId } = useParams();
  const navigate = useNavigate();
  const { currentAdaptation, isGenerating, createAdaptation } = useStore((state) => ({
    currentAdaptation: state.adaptations.currentAdaptation,
    isGenerating: state.adaptations.isGenerating,
    createAdaptation: state.adaptationActions.createAdaptation,
  }));

  useEffect(() => {
    if (!currentAdaptation || currentAdaptation.analysis_id !== analysisId) {
      createAdaptation(analysisId);
    }
  }, [analysisId]);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 mb-6"
        >
          <ArrowLeft size={18} /> Back
        </button>

        <h1 className="text-3xl font-bold text-gray-800 mb-8">Adapted CV Preview</h1>

        <div className="space-y-6">
          <CVPreviewHTML
            html={currentAdaptation?.html_content}
            isLoading={isGenerating}
          />

          {currentAdaptation && !isGenerating && (
            <div className="flex gap-4">
              <PDFDownloadButton adaptationId={currentAdaptation.id} />
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
