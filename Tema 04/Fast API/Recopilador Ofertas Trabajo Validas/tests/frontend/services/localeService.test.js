import { describe, it, expect, beforeEach, vi } from 'vitest';
import { detectBrowserLocale, initLocale, changeLocale, syncLocaleToProfile } from '../../../frontend/src/services/localeService';
import i18n from '../../../frontend/src/i18n';

describe('localeService', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('detectBrowserLocale', () => {
    it('should return "en" when browser language starts with "en"', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'en-US',
        configurable: true,
      });
      expect(detectBrowserLocale()).toBe('en');
    });

    it('should return "es" when browser language starts with "es"', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'es-ES',
        configurable: true,
      });
      expect(detectBrowserLocale()).toBe('es');
    });

    it('should return "es" as fallback for unknown language', () => {
      Object.defineProperty(navigator, 'language', {
        value: 'fr-FR',
        configurable: true,
      });
      expect(detectBrowserLocale()).toBe('es');
    });

    it('should return localStorage value if set', () => {
      localStorage.setItem('locale', 'en');
      Object.defineProperty(navigator, 'language', {
        value: 'es-ES',
        configurable: true,
      });
      expect(detectBrowserLocale()).toBe('en');
    });
  });

  describe('initLocale', () => {
    it('should initialize with detected locale', async () => {
      Object.defineProperty(navigator, 'language', {
        value: 'en-US',
        configurable: true,
      });
      const locale = await initLocale();
      expect(locale).toBe('en');
      expect(localStorage.getItem('locale')).toBe('en');
    });

    it('should use profile preferred_language if provided', async () => {
      Object.defineProperty(navigator, 'language', {
        value: 'es-ES',
        configurable: true,
      });
      const profile = { preferred_language: 'en' };
      const locale = await initLocale(profile);
      expect(locale).toBe('en');
    });

    it('should fallback to "es" if profile language is invalid', async () => {
      const profile = { preferred_language: 'fr' };
      const locale = await initLocale(profile);
      expect(locale).toBe('es');
    });
  });

  describe('changeLocale', () => {
    it('should reject invalid locales', async () => {
      const mockStore = {
        localeActions: {
          setLocale: vi.fn(),
          setSyncing: vi.fn(),
          setSyncError: vi.fn(),
        },
        auth: { token: null },
      };
      await changeLocale('fr', mockStore);
      expect(mockStore.localeActions.setLocale).not.toHaveBeenCalled();
    });

    it('should update localStorage and call setLocale', async () => {
      const mockStore = {
        localeActions: {
          setLocale: vi.fn(),
          setSyncing: vi.fn(),
          setSyncError: vi.fn(),
        },
        auth: { token: null },
      };
      await changeLocale('en', mockStore);
      expect(localStorage.getItem('locale')).toBe('en');
      expect(mockStore.localeActions.setLocale).toHaveBeenCalledWith('en');
    });
  });

  describe('syncLocaleToProfile', () => {
    it('should not sync if user is not authenticated', async () => {
      const mockStore = {
        localeActions: {
          setSyncing: vi.fn(),
          setSyncError: vi.fn(),
        },
        auth: { token: null },
      };
      await syncLocaleToProfile('en', mockStore);
      expect(mockStore.localeActions.setSyncing).not.toHaveBeenCalled();
    });
  });
});
