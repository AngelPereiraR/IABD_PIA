import { Spinner } from '../../../shared/components';
import { useLocale } from '../../../hooks/useLocale';

export function CVPreviewHTML({ html, isLoading }) {
  const { t } = useLocale();
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-800">{t('pages.adaptations.cvPreview')}</h3>
      </div>
      <div className="p-6">
        {isLoading ? (
          <Spinner message={t('pages.adaptations.generatingAdapted')} size={32} />
        ) : html ? (
          <div
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <p className="text-gray-600 text-center py-8">{t('pages.adaptations.noPreviewAvailable')}</p>
        )}
      </div>
    </div>
  );
}
