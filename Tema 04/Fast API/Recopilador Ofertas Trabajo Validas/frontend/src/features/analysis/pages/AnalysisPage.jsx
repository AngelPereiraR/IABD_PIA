import { useNavigate } from 'react-router-dom';
import { Layout } from '../../../shared/components';
import { AnalysisForm } from '../components/AnalysisForm';

export function AnalysisPage() {
  const navigate = useNavigate();

  const handleSuccess = (analysis) => {
    navigate(`/dashboard/analysis/${analysis.id}`);
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Analyze Job Offer</h1>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <AnalysisForm onSuccess={handleSuccess} />
        </div>
      </div>
    </Layout>
  );
}
