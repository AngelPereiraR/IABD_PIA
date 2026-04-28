import { Spinner } from '../../../shared/components';

export function CVPreviewHTML({ html, isLoading }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-800">CV Preview</h3>
      </div>
      <div className="p-6">
        {isLoading ? (
          <Spinner message="Generating adapted CV..." size={32} />
        ) : html ? (
          <div
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <p className="text-gray-600 text-center py-8">No preview available</p>
        )}
      </div>
    </div>
  );
}
