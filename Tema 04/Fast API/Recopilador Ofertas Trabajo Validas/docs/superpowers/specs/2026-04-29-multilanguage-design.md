# Multilanguage Support Design Specification

**Date:** 2026-04-29  
**Status:** Design Approved  
**Scope:** Frontend React application with Spanish (ES) and English (EN) support  
**Priority:** Implement immediately (current session)

---

## 1. Overview

Implement professional, robust multilanguage support using React i18next with localStorage and database synchronization. The system will detect the user's browser language preference, allow in-app language switching via Navbar, and persistently store preferences across devices.

**Core Principle:** Fast local updates (localStorage) + eventual consistency with backend (database).

---

## 2. Architecture

### 2.1 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Translation Library | `react-i18next` | Industry-standard i18n for React |
| State Management | Zustand (new slice) | Centralized locale state |
| Service Layer | `localeService.js` | Encapsulate locale logic |
| Hook | `useLocale()` | Clean component access |
| Storage | localStorage + PostgreSQL | Dual-layer persistence |
| API | `PATCH /profile` | Sync preferred_language to DB |

### 2.2 Data Flow

```
App Initialization
    ↓
Detect browser locale (navigator.language) → Fallback: 'es'
    ↓
Check localStorage for override → Use if exists
    ↓
If authenticated: Load profile from DB → Use profile.preferred_language (priority)
    ↓
Initialize i18next + Zustand with detected/loaded locale
    ↓
Render app in selected language

---

User Changes Language in Navbar
    ↓
Call localeActions.changeLocale(newLocale)
    ↓
[IMMEDIATE] Update Zustand state + localStorage + i18next.changeLanguage()
    ↓
[BACKGROUND] syncLocaleToProfile() → PATCH /profile { preferred_language: 'en' }
    ↓
If sync fails: Retry on next change or background interval (no UI blocking)
```

### 2.3 State Shape (Zustand)

```javascript
// In globalStore.js
locale: {
  current: 'es',              // Current language: 'es' or 'en'
  available: ['es', 'en'],    // Available languages
  isSyncing: false,           // Currently syncing to DB
  syncError: null,            // Error message if sync failed
  isInitialized: false        // Whether locale was initialized
}

localeActions: {
  initLocale(),               // Initialize on app startup
  changeLocale(locale),       // User changes language
  syncLocaleToProfile(),      // Sync to DB
  loadLocaleFromProfile(profile), // Load from user profile
  setInitialized(bool)
}
```

---

## 3. File Structure

### 3.1 New Files to Create

```
frontend/src/
├── locales/
│   ├── es.json              # Spanish translations
│   └── en.json              # English translations
├── services/
│   └── localeService.js     # Locale logic (detect, init, sync)
├── hooks/
│   └── useLocale.js         # Hook for accessing t() function
└── i18n.js                  # i18next configuration
```

### 3.2 Files to Modify

| File | Change |
|------|--------|
| `globalStore.js` | Add locale slice + localeActions |
| `main.jsx` or `App.jsx` | Call `initLocale()` on startup |
| `Navbar.jsx` | Add language selector (ES/EN dropdown or buttons) |
| All UI components | Replace hardcoded strings with `t('namespace.key')` |

---

## 4. Implementation Details

### 4.1 localeService.js

**Functions:**

```javascript
// Detect browser's preferred language
detectBrowserLocale() → 'es' | 'en' | 'es' (default)

// Initialize i18next and Zustand on app load
initLocale(profile?) → Promise<void>
  - Detect browser locale
  - Check localStorage
  - If authenticated, load from profile (priority)
  - Initialize i18next
  - Update Zustand

// Change language (called from Navbar)
changeLocale(locale) → Promise<void>
  - Validate locale is in ['es', 'en']
  - Update Zustand immediately
  - Update localStorage immediately
  - Call i18next.changeLanguage()
  - Trigger async sync to DB (don't await)

// Sync to backend (background, non-blocking)
syncLocaleToProfile() → Promise<void>
  - Check if authenticated
  - PATCH /profile { preferred_language: current }
  - On success: clear syncError
  - On failure: set syncError, will retry on next change

// Load locale from user profile
loadLocaleFromProfile(profile) → void
  - Extract profile.preferred_language
  - Update Zustand
  - Call i18next.changeLanguage()
```

### 4.2 useLocale Hook

```javascript
export function useLocale() {
  const { locale } = useStore();
  const { i18n, t } = useTranslation();
  
  return {
    t,                    // Function to translate: t('key.subkey')
    locale: locale.current,  // Current language
    available: locale.available,
    isSyncing: locale.isSyncing,
    changeLocale: (newLocale) => 
      useStore().localeActions.changeLocale(newLocale)
  };
}
```

**Usage in components:**

```jsx
import { useLocale } from '../hooks/useLocale';

export function LoginPage() {
  const { t } = useLocale();
  
  return (
    <div>
      <h1>{t('auth.login')}</h1>
      <input placeholder={t('auth.email')} />
      <button>{t('common.submit')}</button>
    </div>
  );
}
```

### 4.3 Translation Files Structure

**es.json:**

```json
{
  "nav": {
    "home": "Inicio",
    "dashboard": "Panel",
    "profile": "Perfil",
    "logout": "Cerrar sesión",
    "language": "Idioma"
  },
  "auth": {
    "login": "Iniciar sesión",
    "register": "Registrarse",
    "email": "Correo electrónico",
    "password": "Contraseña",
    "confirmPassword": "Confirmar contraseña",
    "loginError": "Correo o contraseña incorrectos",
    "registerError": "Error en el registro",
    "submit": "Enviar"
  },
  "common": {
    "loading": "Cargando...",
    "error": "Error",
    "success": "Éxito",
    "cancel": "Cancelar",
    "save": "Guardar",
    "delete": "Eliminar",
    "edit": "Editar",
    "close": "Cerrar"
  },
  "cv": {
    "upload": "Subir CV",
    "delete": "Eliminar CV",
    "uploading": "Subiendo CV...",
    "uploadSuccess": "CV subido correctamente"
  },
  "analysis": {
    "create": "Crear análisis",
    "analyzing": "Analizando...",
    "title": "Análisis de ofertas"
  },
  "adaptations": {
    "generate": "Generar adaptación",
    "generating": "Generando...",
    "download": "Descargar PDF"
  }
}
```

**en.json:** Same structure, English translations.

### 4.4 Navbar Language Selector

```jsx
// In Navbar.jsx
import { useLocale } from '../hooks/useLocale';

export function Navbar() {
  const { locale, changeLocale, isSyncing } = useLocale();
  
  return (
    <nav>
      {/* Existing nav items */}
      
      <div className="language-selector">
        <button 
          onClick={() => changeLocale('es')}
          className={locale === 'es' ? 'active' : ''}
        >
          ES
        </button>
        <button 
          onClick={() => changeLocale('en')}
          className={locale === 'en' ? 'active' : ''}
        >
          EN
        </button>
        {isSyncing && <Spinner size="sm" />}
      </div>
    </nav>
  );
}
```

---

## 5. Initialization Flow

### 5.1 App.jsx or main.jsx

```javascript
import { useEffect } from 'react';
import { initLocale } from './services/localeService';
import useStore from './stores/globalStore';

export function App() {
  const { profile } = useStore().profile;
  
  useEffect(() => {
    // Initialize locale on app load, passing profile if available
    initLocale(profile?.data);
  }, []);
  
  // Rest of app...
}
```

### 5.2 On User Login

```javascript
// In globalStore.js login action, after setting user:
get().profileActions.loadProfile();
get().localeActions.loadLocaleFromProfile(response.data);
```

---

## 6. Scope: What Gets Translated vs. What Doesn't

### ✅ Translate (UI/UX)

- Navbar items, buttons, links
- Form labels and placeholders
- Error and success messages
- Modal titles and descriptions
- Landing page content
- Auth flow (login, register, password reset)
- Dashboard labels
- Sidebar navigation

### ❌ Do NOT Translate (Content Integrity)

- CV preview text (user's actual CV data)
- Job offer details from scraper (original language from web)
- Analysis results and scoring explanations (from AI backend)
- User-generated content (names, emails, etc.)

**Rationale:** Translating sensitive content (CV, job offers, AI analysis) could distort meaning and break the analysis pipeline.

---

## 7. Testing Strategy

### 7.1 Unit Tests

- `localeService.test.js`
  - `detectBrowserLocale()` returns correct locale
  - `changeLocale()` updates Zustand and localStorage
  - `syncLocaleToProfile()` calls API correctly
  - Retry logic on sync failure

- `useLocale.test.js`
  - Hook returns `t()` function
  - `changeLocale()` is callable
  - Values sync with Zustand

### 7.2 Integration Tests

- Navbar language selector
  - Click ES/EN button → UI updates to new language
  - localStorage reflects change
  - Zustand state updates
  - API call triggered (can mock)

- Profile sync
  - Change language while authenticated
  - Verify PATCH /profile is called
  - Verify localStorage persists across page reload

### 7.3 Validation

- JSON consistency: both es.json and en.json have same keys
- No missing translations (linting)
- All hardcoded strings replaced with `t()` calls

---

## 8. Migration Plan

### Phase 0: Backend Database (Pre-Phase 1)
- **Check if `users` table has `preferred_language` column**
- If missing: Create Alembic migration to add it
  ```bash
  alembic revision --autogenerate -m "Add preferred_language to users table"
  alembic upgrade head
  ```
- If exists: No action needed
- **Update user model** (e.g., in `src/models/user.py`) to include `preferred_language` field

### Phase 1: Frontend Setup (Day 1)
- Create locales/, services/, hooks/ directories
- Create es.json and en.json with basic keys
- Create i18n.js configuration
- Create localeService.js and useLocale.js
- Add locale slice to Zustand
- Call initLocale() in App.jsx

### Phase 2: Navbar Integration (Day 1-2)
- Add language selector to Navbar
- Test language switching works locally
- Verify localStorage updates

### Phase 3: Component Migration (Day 2-3)
- Migrate by feature area:
  1. auth/ (LoginPage, RegisterPage, LoginForm, RegisterForm)
  2. landing/ (LandingPage)
  3. shared/ (Layout, Footer, common components)
  4. dashboard/ (DashboardPage)
  5. cv/, analysis/, adaptations/ features

### Phase 4: Testing & Validation (Day 3-4)
- Run unit tests
- Verify JSON consistency
- Test sync to profile.preferred_language
- Cross-browser testing (different navigator.language settings)

---

## 9. Backend Integration

### 9.1 API Changes

**Existing:** `PATCH /profile` endpoint (modify user profile)

**Expected field:** `preferred_language` (string: 'es' | 'en')

**No new endpoints needed.** Reuse existing profile update endpoint.

### 9.2 Database Migration (Alembic)

**Required:** The `users` table must have a `preferred_language` column (VARCHAR, default 'es').

**If column doesn't exist:**

1. Create Alembic migration:
   ```bash
   alembic revision --autogenerate -m "Add preferred_language to users table"
   ```

2. Or create manually:
   ```python
   # In migration file (alembic/versions/...)
   def upgrade():
       op.add_column('users', 
           sa.Column('preferred_language', sa.String(5), 
                     server_default='es', nullable=False))
   
   def downgrade():
       op.drop_column('users', 'preferred_language')
   ```

3. Run migration:
   ```bash
   alembic upgrade head
   ```

**Column specs:**
- Type: VARCHAR(5) or String
- Default: 'es'
- Nullable: False
- Values: 'es' or 'en' (but no constraint for future languages)

---

## 10. Future Extensibility

### 10.1 Adding New Languages

1. Create `fr.json` in `locales/`
2. Add 'fr' to `locale.available` in Zustand
3. Update detectBrowserLocale() logic
4. Update Navbar selector to include FR button
5. Translate content

### 10.2 Translation Management (Free Options)

Once you have 5+ languages, consider:
- **Weblate** (open source, self-hosted or managed — completely free)
- **Pontoon** (Mozilla's translation platform — free)
- **Git-based workflow** (simplest) — JSON in repo, PRs for new translations
- CI/CD to validate JSON structure (GitHub Actions — free)
- Automated validation: check both JSON files have identical keys

**Avoid:** Crowdin (paid), OneSky (paid) — stick to free/open-source tools for now.

---

## 11. Error Handling

### 11.1 Sync Failures

If `PATCH /profile` fails (network, 401, 500):
- Don't block UI (user language change is instant anyway)
- Set `syncError` in Zustand
- Retry on next language change
- Log error for debugging

### 11.2 Missing Translations

If a key doesn't exist in the current JSON:
- i18next shows the key name as fallback (e.g., `'auth.missing_key'`)
- Console warning in development
- Add the key to both JSON files immediately

---

## 12. Success Criteria

✅ User can switch between ES and EN from Navbar  
✅ Language persists in localStorage  
✅ Language syncs to DB (profile.preferred_language)  
✅ On new device, language loads from user profile  
✅ All UI text translated except sensitive content  
✅ No hardcoded strings in component files  
✅ Browser locale auto-detected on first visit  
✅ Tests pass (unit + integration)  
✅ No performance degradation  

---

## 13. Dependencies to Install

```bash
npm install react-i18next i18next i18next-browser-languagedetector
```

**Why these:**
- `react-i18next` — React bindings for i18next
- `i18next` — Core library
- `i18next-browser-languagedetector` — Auto-detect browser language

---

## 14. Rollback Plan

If issues arise:
1. Remove Navbar language selector
2. Default all users to 'es'
3. Keep infrastructure in place for future use
4. No code deletion needed

---

**End of Specification**
