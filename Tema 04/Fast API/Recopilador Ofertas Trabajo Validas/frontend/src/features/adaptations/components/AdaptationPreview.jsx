import { useState, useEffect } from 'react';
import { FileText } from 'lucide-react';

export function AdaptationPreview({ adaptation, isLoading }) {
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
  const filename = `${adaptation.job_title} - Adapted CV`;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-200 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <FileText size={32} className="text-indigo-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{filename}</h3>
            <p className="text-sm text-gray-500">Adapted CV - {adaptation.company}</p>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center">
          <p className="text-gray-600">Generating preview...</p>
        </div>
      ) : (
        <div className="bg-gray-50 p-4 space-y-4">
          {/* Height Controls */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex gap-2">
              <label className="text-sm font-medium text-gray-700">Height:</label>
              <button
                onClick={() => setPreviewHeight(400)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 400
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
                }`}
              >
                S
              </button>
              <button
                onClick={() => setPreviewHeight(600)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 600
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
                }`}
              >
                M
              </button>
              <button
                onClick={() => setPreviewHeight(800)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 800
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
                }`}
              >
                L
              </button>
              <button
                onClick={() => setPreviewHeight(1200)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewHeight === 1200
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
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
                className="w-32"
              />
              <span className="text-sm text-gray-600 w-14">{previewHeight}px</span>
            </div>
          </div>

          {/* Width Controls */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex gap-2">
              <label className="text-sm font-medium text-gray-700">Width:</label>
              <button
                onClick={() => setPreviewWidth(75)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewWidth === 75
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
                }`}
              >
                75%
              </button>
              <button
                onClick={() => setPreviewWidth(90)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewWidth === 90
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
                }`}
              >
                90%
              </button>
              <button
                onClick={() => setPreviewWidth(100)}
                className={`px-3 py-1 rounded text-sm transition ${
                  previewWidth === 100
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white border border-gray-300 hover:bg-gray-100'
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
                className="w-32"
              />
              <span className="text-sm text-gray-600 w-14">{previewWidth}%</span>
            </div>
          </div>

          {/* Preview Container */}
          <div className="pt-6" style={{ width: `${previewWidth}%`, margin: '0 auto' }}>
            <iframe
              src={cvUrl}
              title="Adapted CV Preview"
              className="w-full border border-gray-300 rounded"
              style={{ height: `${previewHeight}px` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
