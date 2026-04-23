import { useEffect } from 'react';
import { Layout } from '../../../shared/components';
import { CVUpload } from '../components/CVUpload';
import { CVPreview } from '../components/CVPreview';
import useStore from '../../../stores/globalStore';

export function CVPage() {
  const { fetchCurrentCV, currentCV } = useStore((state) => ({
    fetchCurrentCV: state.cvActions.fetchCurrentCV,
    currentCV: state.cv.currentCV,
  }));

  useEffect(() => {
    fetchCurrentCV();
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Manage Your CV</h1>
        <div className="space-y-6">
          {currentCV && <CVPreview />}
          <CVUpload />
        </div>
      </div>
    </Layout>
  );
}
