import { X } from 'lucide-react';
import { useEffect } from 'react';
import { useLocale } from '../../hooks/useLocale';

const scrollbarStyles = `
  .modal-content::-webkit-scrollbar {
    width: 8px;
  }
  .modal-content::-webkit-scrollbar-track {
    background: #2A2A2A;
  }
  .modal-content::-webkit-scrollbar-thumb {
    background: #3D3D3D;
    border-radius: 0;
  }
  .modal-content::-webkit-scrollbar-thumb:hover {
    background: #C9A84C;
  }
  .modal-content {
    scrollbar-color: #3D3D3D #2A2A2A;
    scrollbar-width: thin;
  }
`;

export function Modal({ isOpen, onClose, title, children, size = 'md' }) {
  const { t } = useLocale();

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-2xl',
    '2xl': 'max-w-4xl',
  };

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 overflow-y-auto" onClick={onClose}>
        <div
          className={`bg-brand-gray border-2 border-brand-gray-light w-full ${sizeClasses[size]} max-h-[95vh] overflow-hidden flex flex-col my-auto`}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between px-6 py-5 bg-brand-black border-b-2 border-brand-gold/30 flex-shrink-0">
            <h2 className="text-2xl font-display font-black text-brand-white">{title}</h2>
            <button
              onClick={onClose}
              className="text-brand-white/70 hover:text-brand-gold transition-colors flex-shrink-0 ml-4"
              aria-label={t('common.close')}
            >
              <X size={24} />
            </button>
          </div>
          <div className="modal-content overflow-y-auto flex-1 px-6 py-6 bg-brand-gray text-brand-white/70">
            {children}
          </div>
        </div>
      </div>
    </>
  );
}
