import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import useStore from '../../../stores/globalStore';
import { Link, Search } from 'lucide-react';

const schema = z.object({
  type: z.enum(['url', 'text']),
  content: z.string().min(10, 'Content too short'),
});

export function AnalysisForm({ onSuccess }) {
  const [activeTab, setActiveTab] = useState('url');
  const { createAnalysis, isAnalyzing } = useStore((state) => ({
    createAnalysis: state.analysisActions.createAnalysis,
    isAnalyzing: state.analysis.isAnalyzing,
  }));
  const { register, handleSubmit, formState: { errors }, reset } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { type: 'url' },
  });

  const onSubmit = async (data) => {
    const input = {
      type: data.type,
      [data.type === 'url' ? 'url' : 'text']: data.content,
    };
    const result = await createAnalysis(input);
    if (result.success) {
      reset();
      onSuccess?.(result.data);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="flex gap-2 mb-4">
        <button
          type="button"
          onClick={() => setActiveTab('url')}
          className={`px-4 py-2 rounded font-medium ${
            activeTab === 'url' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'
          }`}
        >
          <Link size={16} className="inline mr-2" /> URL
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('text')}
          className={`px-4 py-2 rounded font-medium ${
            activeTab === 'text' ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'
          }`}
        >
          <Search size={16} className="inline mr-2" /> Text
        </button>
      </div>

      <input type="hidden" {...register('type')} value={activeTab} />

      <div>
        {activeTab === 'url' && (
          <>
            <label className="block text-sm font-medium text-gray-700 mb-2">Job Offer URL</label>
            <input
              {...register('content')}
              type="url"
              placeholder="https://linkedin.com/jobs/..."
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </>
        )}
        {activeTab === 'text' && (
          <>
            <label className="block text-sm font-medium text-gray-700 mb-2">Offer Description</label>
            <textarea
              {...register('content')}
              placeholder="Paste the job offer text here..."
              rows="6"
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </>
        )}
        {errors.content && <p className="text-red-500 text-sm mt-1">{errors.content.message}</p>}
      </div>

      <button
        type="submit"
        disabled={isAnalyzing}
        className="w-full px-4 py-2 bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 disabled:bg-gray-400"
      >
        {isAnalyzing ? 'Analyzing...' : 'Analyze Offer'}
      </button>
    </form>
  );
}
