import { Modal } from '../../../shared/components/Modal';
import { useLocale } from '../../../hooks/useLocale';
import termsES from '../../../locales/terms.es.json';
import termsEN from '../../../locales/terms.en.json';

export function TermsModal({ isOpen, onClose }) {
  const { locale } = useLocale();
  const terms = locale === 'es' ? termsES : termsEN;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={terms.title} size="2xl">
      <div className="space-y-4 text-brand-white/70 leading-relaxed font-mono">
        {Object.entries(terms.sections).map(([key, section]) => (
          <section key={key} className="border-b border-brand-gold/20 pb-4 last:border-b-0">
            <h3 className="font-display font-bold text-brand-gold mb-3 text-2xl">{section.title}</h3>
            {section.intro && <p className="mb-3 text-sm">{section.intro}</p>}
            {section.content && <p className="text-sm">{section.content}</p>}
            {section.items && (
              <ul className="list-disc pl-6 space-y-1 mt-3">
                {section.items.map((item, idx) => (
                  <li key={idx} className="text-sm">{item}</li>
                ))}
              </ul>
            )}
            {section.subsections && (
              <div className="mt-4 space-y-3 pl-4 border-l-4 border-brand-gold">
                {Object.entries(section.subsections).map(([subKey, subsection]) => (
                  <div key={subKey}>
                    <p className="font-display font-bold text-brand-white/90 mb-2 text-lg">{subsection.title}</p>
                    {subsection.intro && <p className="mb-2 text-sm">{subsection.intro}</p>}
                    {subsection.content && <p className="text-sm">{subsection.content}</p>}
                    {subsection.items && (
                      <ul className="list-disc pl-6 mt-2 space-y-1">
                        {subsection.items.map((item, idx) => (
                          <li key={idx} className="text-sm">{item}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        ))}

        <section className="pt-4 border-t border-brand-gold/30">
          <p className="text-xs text-brand-white/40">
            {terms.lastUpdated} {new Date().toLocaleDateString(locale === 'es' ? 'es-ES' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </section>
      </div>
    </Modal>
  );
}
