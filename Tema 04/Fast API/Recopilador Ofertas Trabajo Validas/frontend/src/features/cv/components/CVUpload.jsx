import { useRef, useState } from 'react';
import useStore from '../../../stores/globalStore';
import { Upload, CheckCircle } from 'lucide-react';

export function CVUpload() {
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
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Upload Your CV</h3>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload size={32} className="mx-auto text-gray-400 mb-2" />
        <p className="text-gray-700 font-medium">Drag and drop your PDF here</p>
        <p className="text-sm text-gray-500">or click to select a file</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          disabled={isUploading}
          className="hidden"
        />
      </div>
      {error && <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded">{error}</div>}
      {isUploading && <div className="mt-4 p-3 bg-blue-50 text-blue-700 text-sm rounded">Uploading...</div>}
    </div>
  );
}
