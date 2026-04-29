import { useTranslation } from 'react-i18next';
import useStore from '../stores/globalStore';
import { changeLocale } from '../services/localeService';

/**
 * Hook for accessing translations and locale state
 * Usage: const { t, locale, changeLocale } = useLocale();
 */
export function useLocale() {
  const { i18n, t } = useTranslation();
  const { locale: localeState, localeActions } = useStore();
  const store = useStore();

  const handleChangeLocale = async (newLocale) => {
    await changeLocale(newLocale, store);
  };

  return {
    t,                              // Translation function
    locale: localeState.current,    // Current language ('es' or 'en')
    available: localeState.available, // Available languages
    isSyncing: localeState.isSyncing, // Currently syncing to DB
    syncError: localeState.syncError,  // Error message if sync failed
    changeLocale: handleChangeLocale,  // Change language function
    i18n,                           // i18next instance (if needed)
  };
}
