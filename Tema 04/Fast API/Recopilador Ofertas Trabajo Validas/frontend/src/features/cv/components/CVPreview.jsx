import useStore from '../../../stores/globalStore';
import { FileText, Trash2 } from 'lucide-react';

export function CVPreview() {
  const { currentCV, deleteCV } = useStore((state) => ({
    currentCV: state.cv.currentCV,
    deleteCV: state.cvActions.deleteCV,
  }));

  if (!currentCV) {
    return null;
  }

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete your CV?')) {
      await deleteCV();
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Current CV</h3>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <FileText size={32} className="text-indigo-600" />
          <div>
            <p className="font-medium text-gray-800">{currentCV.filename || 'CV Document'}</p>
            <p className="text-sm text-gray-500">
              {currentCV.size ? `${(currentCV.size / 1024).toFixed(2)} KB` : 'Uploaded'}
            </p>
          </div>
        </div>
        <button
          onClick={handleDelete}
          className="flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded transition"
        >
          <Trash2 size={18} />
          Delete
        </button>
      </div>
    </div>
  );
}
