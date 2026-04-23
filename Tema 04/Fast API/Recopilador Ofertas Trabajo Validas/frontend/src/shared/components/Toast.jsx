import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

export function Toast({ toast, onClose }) {
  const bgColor = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    warning: 'bg-yellow-50 border-yellow-200',
    info: 'bg-blue-50 border-blue-200',
  }[toast.type] || 'bg-gray-50 border-gray-200';

  const textColor = {
    success: 'text-green-800',
    error: 'text-red-800',
    warning: 'text-yellow-800',
    info: 'text-blue-800',
  }[toast.type] || 'text-gray-800';

  const Icon = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertCircle,
    info: Info,
  }[toast.type] || Info;

  return (
    <div className={`${bgColor} border rounded-lg p-4 flex items-start gap-3 mb-2`}>
      <Icon size={20} className={textColor} />
      <div className="flex-1">
        <p className={`${textColor} text-sm font-medium`}>{toast.message}</p>
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
