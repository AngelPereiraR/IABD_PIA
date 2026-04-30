import { useEffect } from 'react';
import { Layout, Spinner } from '../../../shared/components';
import { CVUpload } from '../components/CVUpload';
import { CVPreview } from '../components/CVPreview';
import useStore from '../../../stores/globalStore';
import { useLocale } from '../../../hooks/useLocale';

export function CVPage() {
  const { t } = useLocale();
  const { fetchCurrentCV, currentCV, isLoading } = useStore((state) => ({
    fetchCurrentCV: state.cvActions.fetchCurrentCV,
    currentCV: state.cv.currentCV,
    isLoading: state.cv.isLoading,
  }));

  useEffect(() => {
    fetchCurrentCV();
  }, []);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-display font-bold text-brand-white mb-8">{t('pages.cv.uploadCV')}</h1>
        <div className="space-y-6">
          {isLoading ? (
            <div className="bg-brand-gray border-2 border-brand-gray-light p-8 min-h-64">
              <Spinner message={t('common.loading')} size={32} />
            </div>
          ) : currentCV ? (
            <CVPreview />
          ) : null}
          <CVUpload />
        </div>
      </div>
    </Layout>
  );
}
