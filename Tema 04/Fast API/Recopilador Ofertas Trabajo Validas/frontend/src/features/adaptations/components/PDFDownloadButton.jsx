import { useState } from 'react';
import { Download, Loader } from 'lucide-react';
import useStore from '../../../stores/globalStore';

export function PDFDownloadButton({ adaptationId }) {
  const { downloadPDF } = useStore((state) => ({
    downloadPDF: state.adaptationActions.downloadPDF,
  }));
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    const result = await downloadPDF(adaptationId);
    setIsDownloading(false);
    if (!result.success) {
      alert(result.error || 'Failed to download PDF');
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={isDownloading}
      className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-gray-400 transition"
    >
      {isDownloading ? (
        <>
          <Loader size={18} className="animate-spin" /> Downloading...
        </>
      ) : (
        <>
          <Download size={18} /> Download PDF
        </>
      )}
    </button>
  );
}
