import i18n from '../i18n';
import { profileService } from './profileService'; // Assuming this exists

/**
 * Detect browser's preferred language
 * Returns 'es' or 'en', with 'es' as fallback
 */
export function detectBrowserLocale() {
  const browserLang = navigator.language || navigator.userLanguage;

  if (browserLang.startsWith('en')) {
    return 'en';
  }
  if (browserLang.startsWith('es')) {
    return 'es';
  }

  // Check localStorage for previous choice
  const stored = localStorage.getItem('locale');
  if (stored && ['es', 'en'].includes(stored)) {
    return stored;
  }

  // Fallback to Spanish
  return 'es';
}

/**
 * Initialize i18next with detected or stored locale
 * Called once on app startup
 */
export async function initLocale(userProfile) {
  let locale = 'es';

  // Priority 1: User profile (if authenticated)
  if (userProfile?.preferred_language && ['es', 'en'].includes(userProfile.preferred_language)) {
    locale = userProfile.preferred_language;
  } else {
    // Priority 2: Browser/localStorage
    locale = detectBrowserLocale();
  }

  // Initialize i18next
  if (!i18n.isInitialized) {
    await i18n.init({});
  }

  await i18n.changeLanguage(locale);
  localStorage.setItem('locale', locale);

  return locale;
}

/**
 * Change language (called from Navbar)
 * Updates state immediately, syncs to DB in background
 */
export async function changeLocale(newLocale, store) {
  if (!['es', 'en'].includes(newLocale)) {
    console.error('Invalid locale:', newLocale);
    return;
  }

  // Immediate updates
  localStorage.setItem('locale', newLocale);
  await i18n.changeLanguage(newLocale);
  store.localeActions.setLocale(newLocale);

  // Background sync (don't await, don't block UI)
  syncLocaleToProfile(newLocale, store);
}

/**
 * Sync locale to user profile (background, non-blocking)
 */
export async function syncLocaleToProfile(locale, store) {
  if (!store.auth.token) {
    // Not authenticated, nothing to sync
    return;
  }

  store.localeActions.setSyncing(true);

  try {
    await profileService.updateProfile({ preferred_language: locale });
    store.localeActions.setSyncError(null);
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to sync language preference';
    store.localeActions.setSyncError(message);
    console.error('Locale sync error:', error);
  } finally {
    store.localeActions.setSyncing(false);
  }
}

/**
 * Load locale from user profile
 * Called after profile is loaded
 */
export async function loadLocaleFromProfile(profile, store) {
  if (!profile?.preferred_language) {
    return;
  }

  const locale = profile.preferred_language;
  if (['es', 'en'].includes(locale)) {
    localStorage.setItem('locale', locale);
    await i18n.changeLanguage(locale);
    store.localeActions.setLocale(locale);
  }
}
