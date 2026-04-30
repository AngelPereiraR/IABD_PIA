import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

export function Toast({ toast, onClose }) {
  const bgColor = {
    success: 'bg-green-950/40 border-green-800/50',
    error: 'bg-red-950/40 border-red-800/50',
    warning: 'bg-yellow-950/40 border-yellow-800/50',
    info: 'bg-blue-950/40 border-blue-800/50',
  }[toast.type] || 'bg-brand-gray border-brand-gray-light';

  const textColor = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  }[toast.type] || 'text-brand-white';

  const Icon = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertCircle,
    info: Info,
  }[toast.type] || Info;

  return (
    <div className={`${bgColor} border border-2 p-4 flex items-start gap-3 mb-2`}>
      <Icon size={20} className={textColor} />
      <div className="flex-1">
        <p className={`${textColor} text-sm font-medium font-mono`}>{toast.message}</p>
      </div>
      <button
        onClick={() => onClose(toast.id)}
        className={`${textColor} hover:opacity-75`}
      >
        <X size={18} />
      </button>
    </div>
  );
}

export function ToastContainer({ toasts, onRemove }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 max-w-md z-50">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={onRemove} />
      ))}
    </div>
  );
}
