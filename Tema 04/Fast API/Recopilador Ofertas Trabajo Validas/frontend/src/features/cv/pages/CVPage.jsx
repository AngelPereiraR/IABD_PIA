import { useEffect } from 'react';
import { Layout, Spinner } from '../../../shared/components';
import { CVUpload } from '../components/CVUpload';
import { CVPreview } from '../components/CVPreview';
import useStore from '../../../stores/globalStore';

export function CVPage() {
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
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Manage Your CV</h1>
        <div className="space-y-6">
          {isLoading ? (
            <div className="bg-white rounded-lg border border-gray-200 p-8 min-h-64">
              <Spinner message="Loading your CV..." size={32} />
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
