import { useRef, useState } from 'react';
import useStore from '../../../stores/globalStore';
import { Upload, CheckCircle } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function CVUpload() {
  const { t } = useLocale();
  const fileInputRef = useRef(null);
  const { uploadCV, isUploading, error } = useStore((state) => ({
    uploadCV: state.cvActions.uploadCV,
    isUploading: state.cv.isUploading,
    error: state.cv.error,
  }));
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      await uploadCV(files[0]);
    }
  };

  const handleChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await uploadCV(e.target.files[0]);
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold text-brand-white mb-4">{t('pages.cv.uploadCV')}</h3>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed p-8 text-center cursor-pointer transition ${
          dragActive ? 'border-brand-gold bg-brand-gold/10' : 'border-brand-gold hover:bg-brand-gray/50'
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload size={32} className="mx-auto text-brand-gold mb-2" />
        <p className="text-brand-white font-medium">{t('pages.cv.dragDrop')}</p>
        <p className="text-sm text-brand-white/70 font-mono">{t('pages.cv.selectFile')}</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          disabled={isUploading}
          className="hidden"
        />
      </div>
      {error && <div className="mt-4 p-3 bg-red-950/40 text-red-400 text-sm border border-red-800/50 font-mono">{error}</div>}
      {isUploading && <div className="mt-4 p-3 bg-blue-950/40 text-blue-400 text-sm border border-blue-800/50 font-mono">{t('cv.uploading')}</div>}
    </div>
  );
}
