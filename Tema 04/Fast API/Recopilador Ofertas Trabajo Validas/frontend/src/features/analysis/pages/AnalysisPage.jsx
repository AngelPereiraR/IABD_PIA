import { useNavigate } from 'react-router-dom';
import { Layout } from '../../../shared/components';
import { AnalysisForm } from '../components/AnalysisForm';
import { useLocale } from '../../../hooks/useLocale';

export function AnalysisPage() {
  const { t } = useLocale();
  const navigate = useNavigate();

  const handleSuccess = (analysis) => {
    navigate(`/dashboard/analysis/${analysis.id}`);
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-display font-bold text-brand-white mb-8">{t('pages.analysis.analyzeJobOffer')}</h1>
        <div className="bg-brand-gray p-6 border-2 border-brand-gray-light">
          <AnalysisForm onSuccess={handleSuccess} />
        </div>
      </div>
    </Layout>
  );
}
