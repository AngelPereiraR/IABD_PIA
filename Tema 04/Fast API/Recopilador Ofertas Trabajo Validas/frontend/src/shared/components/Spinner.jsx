import { Loader } from 'lucide-react';

export function Spinner({ size = 32, text = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <Loader size={size} className="text-indigo-600 animate-spin mb-2" />
      {text && <p className="text-gray-600 text-sm">{text}</p>}
    </div>
  );
}
