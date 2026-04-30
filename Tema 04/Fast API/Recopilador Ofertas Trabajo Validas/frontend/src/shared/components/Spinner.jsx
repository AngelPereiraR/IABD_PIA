export function Spinner({
  message = null,
  size = 48,
  fullHeight = false,
  inline = false,
  color = 'text-brand-gold',
  containerClassName = '',
}) {
  const sizeMap = {
    16: 'h-4 w-4',
    18: 'h-5 w-5',
    24: 'h-6 w-6',
    32: 'h-8 w-8',
    48: 'h-12 w-12',
  };

  const sizeClass = sizeMap[size] || `h-${Math.ceil(size / 4)} w-${Math.ceil(size / 4)}`;

  const spinnerSvg = (
    <svg
      className={`animate-spin ${sizeClass} ${color}`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
    >
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="1" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.8" transform="rotate(30 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.7" transform="rotate(60 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.6" transform="rotate(90 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" transform="rotate(120 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4" transform="rotate(150 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.3" transform="rotate(180 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.2" transform="rotate(210 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.15" transform="rotate(240 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.1" transform="rotate(270 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.05" transform="rotate(300 12 12)" />
      <line x1="12" y1="2" x2="12" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.025" transform="rotate(330 12 12)" />
    </svg>
  );

  if (inline) {
    return <>{spinnerSvg}</>;
  }

  const baseClassName = 'flex flex-col items-center justify-center';
  const heightClassName = fullHeight ? 'h-screen' : 'py-8';
  const finalClassName = `${baseClassName} ${heightClassName} ${containerClassName}`;

  return (
    <div className={finalClassName}>
      {spinnerSvg}
      {message && <p className="text-brand-white/70 text-lg mt-4 font-mono">{message}</p>}
    </div>
  );
}
