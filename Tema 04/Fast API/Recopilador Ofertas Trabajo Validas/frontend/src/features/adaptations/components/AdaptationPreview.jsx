import { useState, useEffect } from 'react';
import { FileText } from 'lucide-react';
import { useLocale } from '../../../hooks/useLocale';

export function AdaptationPreview({ adaptation, isLoading }) {
  const { t } = useLocale();
  const [previewHeight, setPreviewHeight] = useState(800);
  const [previewWidth, setPreviewWidth] = useState(100);
  const [maxHeight, setMaxHeight] = useState(1200);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerHeight < 800) {
        setMaxHeight(800);
      } else if (window.innerHeight < 1200) {
        setMaxHeight(1000);
      } else {
        setMaxHeight(Math.max(1400, window.innerHeight - 200));
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!adaptation || !adaptation.adapted_cv_url) {
    return null;
  }

  const cvUrl = adaptation.adapted_cv_url;
  const filename = `${adaptation.job_title} - ${t('pages.adaptations.adaptedCV')}`;

  return (
    <div className="bg-brand-gray border-2 border-brand-gray-light overflow-hidden">
      <div className="p-6 border-b-2 border-brand-gray-light flex items-start justify-between">
        <div className="flex items-center gap-3">
          <FileText size={32} className="text-brand-gold" />
          <div>
            <h3 className="text-lg font-display font-semibold text-brand-white">{filename}</h3>
            <p className="text-sm text-brand-white/70 font-mono">{t('pages.adaptations.adaptedCV')} - {adaptation.company}</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center">
          <p className="text-brand-white/70 font-mono">{t('pages.adaptations.generatingPreview')}</p>
        </div>
      ) : (
        <div className="bg-brand-black/20 p-4 space-y-4">
          {/* Height Controls */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex gap-2">
              <label className="text-sm font-mono font-medium text-brand-white/70">{t('pages.cv.height')}:</label>
              <button
                onClick={() => setPreviewHeight(400)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 400
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                S
              </button>
              <button
                onClick={() => setPreviewHeight(600)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 600
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                M
              </button>
              <button
                onClick={() => setPreviewHeight(800)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 800
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                L
              </button>
              <button
                onClick={() => setPreviewHeight(1200)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 1200
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                XL
              </button>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="300"
                max={maxHeight}
                step="50"
                value={previewHeight}
                onChange={(e) => setPreviewHeight(parseInt(e.target.value))}
                className="w-32 accent-brand-gold"
              />
              <span className="text-sm text-brand-white/70 font-mono w-14">{previewHeight}px</span>
            </div>
          </div>

          {/* Width Controls */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex gap-2">
              <label className="text-sm font-mono font-medium text-brand-white/70">{t('pages.cv.width')}:</label>
              <button
                onClick={() => setPreviewWidth(75)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewWidth === 75
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                75%
              </button>
              <button
                onClick={() => setPreviewWidth(90)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewWidth === 90
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                90%
              </button>
              <button
                onClick={() => setPreviewWidth(100)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewWidth === 100
                    ? 'bg-brand-gold text-brand-black font-bold'
                    : 'bg-brand-black border-2 border-brand-gold text-brand-gold hover:bg-brand-black/50'
                }`}
              >
                100%
              </button>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="50"
                max="100"
                step="5"
                value={previewWidth}
                onChange={(e) => setPreviewWidth(parseInt(e.target.value))}
                className="w-32 accent-brand-gold"
              />
              <span className="text-sm text-brand-white/70 font-mono w-14">{previewWidth}%</span>
            </div>
          </div>

          {/* Preview Container */}
          <div className="pt-6" style={{ width: `${previewWidth}%`, margin: '0 auto' }}>
            <iframe
              src={cvUrl}
              title={t('pages.adaptations.adaptedCVPreview')}
              className="w-full border-2 border-brand-gold"
              style={{ height: `${previewHeight}px` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
