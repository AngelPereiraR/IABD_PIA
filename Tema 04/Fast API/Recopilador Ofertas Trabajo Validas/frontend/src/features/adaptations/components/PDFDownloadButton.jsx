import { useState } from 'react';
import { Download, Loader } from 'lucide-react';
import useStore from '../../../stores/globalStore';
import { useLocale } from '../../../hooks/useLocale';

export function PDFDownloadButton({ adaptationId }) {
  const { t } = useLocale();
  const { downloadPDF } = useStore((state) => ({
    downloadPDF: state.adaptationActions.downloadPDF,
  }));
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    const result = await downloadPDF(adaptationId);
    setIsDownloading(false);
    if (!result.success) {
      alert(result.error || t('pages.adaptations.downloadError'));
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={isDownloading}
      className="flex items-center gap-2 px-6 py-3 bg-transparent text-brand-gold border-2 border-brand-gold font-mono font-bold hover:bg-brand-gold/10 transition disabled:opacity-50"
    >
      {isDownloading ? (
        <>
          <Loader size={18} className="animate-spin" /> {t('common.downloading')}
        </>
      ) : (
        <>
          <Download size={18} /> {t('pages.adaptations.downloadPDF')}
        </>
      )}
    </button>
  );
}
