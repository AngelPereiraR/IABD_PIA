import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import useStore from '../../../stores/globalStore';
import { Link, Search } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

const schema = z.object({
  type: z.enum(['url', 'text']),
  content: z.string().min(10),
});

export function AnalysisForm({ onSuccess }) {
  const { t } = useLocale();
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
    const input = data.type === 'url'
      ? { offer_url: data.content }
      : { offer_text: data.content };
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
          className={`px-4 py-2 font-medium border-2 transition ${
            activeTab === 'url' ? 'bg-brand-gold text-brand-black border-brand-gold' : 'bg-brand-black border-brand-gray-light text-brand-white hover:border-brand-gold'
          }`}
        >
          <Link size={16} className="inline mr-2" /> {t('common.url')}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('text')}
          className={`px-4 py-2 font-medium border-2 transition ${
            activeTab === 'text' ? 'bg-brand-gold text-brand-black border-brand-gold' : 'bg-brand-black border-brand-gray-light text-brand-white hover:border-brand-gold'
          }`}
        >
          <Search size={16} className="inline mr-2" /> {t('pages.analysis.paste')}
        </button>
      </div>

      <input type="hidden" {...register('type')} value={activeTab} />

      <div>
        {activeTab === 'url' && (
          <>
            <label className="block text-sm font-medium text-brand-white/70 mb-2 font-mono">{t('pages.analysis.jobOfferUrl')}</label>
            <input
              {...register('content')}
              type="url"
              placeholder="https://linkedin.com/jobs/..."
              className="w-full px-4 py-2 border-2 border-brand-gray-light bg-brand-black text-brand-white placeholder-brand-white/40 focus:outline-none focus:border-brand-gold transition font-mono"
            />
          </>
        )}
        {activeTab === 'text' && (
          <>
            <label className="block text-sm font-medium text-brand-white/70 mb-2 font-mono">{t('pages.analysis.offerDescription')}</label>
            <textarea
              {...register('content')}
              placeholder={t('pages.analysis.pasteText')}
              rows="6"
              className="w-full px-4 py-2 border-2 border-brand-gray-light bg-brand-black text-brand-white placeholder-brand-white/40 focus:outline-none focus:border-brand-gold transition font-mono"
            />
          </>
        )}
        {errors.content && <p className="text-red-400 text-sm mt-1 font-mono">{errors.content.message || t('common.contentTooShort')}</p>}
      </div>

      <button
        type="submit"
        disabled={isAnalyzing}
        className="w-full px-4 py-2 bg-brand-gold text-brand-black border-2 border-brand-gold font-medium hover:bg-brand-black hover:text-brand-gold transition disabled:opacity-50 font-display font-bold"
      >
        {isAnalyzing ? t('analysis.analyzing') : t('pages.analysis.analyze')}
      </button>
    </form>
  );
}
