# Multilanguage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement professional Spanish/English multilanguage support with localStorage + database persistence, browser auto-detection, and UI language switching via Navbar.

**Architecture:** Zustand slice for locale state + react-i18next for translations + localeService for business logic + useLocale hook for component access. Dual-layer persistence: localStorage (instant) + DB (eventual sync).

**Tech Stack:** react-i18next, Zustand (new slice), localStorage API, PostgreSQL (new column), Alembic (migration)

---

## 🚀 STATUS: IN PROGRESS (10/20 Tasks Complete)

**✅ COMPLETED TASKS (Phases 0-4):**
- ✅ Task 1: Backend database migration (Alembic + User model)
- ✅ Task 2: Dependencies installed (react-i18next, i18next, language detector)
- ✅ Task 3: i18n.js configuration
- ✅ Task 4: Spanish translations (es.json)
- ✅ Task 5: English translations (en.json)
- ✅ Task 6: Locale service (localeService.js)
- ✅ Task 7: useLocale hook
- ✅ Task 8: Zustand locale slice
- ✅ Task 9: App initialization
- ✅ Task 10: Navbar language selector

**⏳ REMAINING TASKS (Phases 5-7):**
- Task 11-15: Component migration (apply `useLocale` pattern to 20+ component files)
- Task 16-18: Unit tests (localeService, useLocale hook, translation consistency)
- Task 19-20: Manual testing + final integration test

**Next Step:** Resume with Task 11 (Migrate Auth Components). Apply the pattern:
```javascript
import { useLocale } from '../hooks/useLocale';
const { t } = useLocale();
// Replace hardcoded strings with t('key.subkey')
```

**Important:** No git commands used (manual commits required after completion)

---

## Phase 0: Backend Database Setup

### Task 1: Add `preferred_language` Column to Users Table

**Files:**
- Create: `alembic/versions/XXXX_XXXXXX_add_preferred_language_to_users.py`
- Modify: `src/models/user.py`

**Context:**
The users table needs a `preferred_language` column to persist language preference across devices. This must be done before frontend can sync to the API.

- [ ] **Step 1: Generate Alembic migration file**

Run:
```bash
cd <project-root>
alembic revision --autogenerate -m "Add preferred_language to users table"
```

This creates a new file in `alembic/versions/` with a timestamp. Note the filename for the next step.

Expected output: `Creating new revision file <alembic/versions/...>`

- [ ] **Step 2: Inspect and edit the migration file**

Open the generated migration file (e.g., `alembic/versions/001_add_preferred_language_to_users.py`).

Replace the `upgrade()` and `downgrade()` functions with:

```python
def upgrade():
    op.add_column('users', 
        sa.Column('preferred_language', sa.String(5), 
                  server_default='es', nullable=False))

def downgrade():
    op.drop_column('users', 'preferred_language')
```

Save the file.

- [ ] **Step 3: Verify migration file syntax**

Run:
```bash
python -m alembic current
```

Expected output: Shows current database revision.

- [ ] **Step 4: Run the migration**

Run:
```bash
alembic upgrade head
```

Expected output: `Running upgrade -> <revision_id>, Add preferred_language to users table`

- [ ] **Step 5: Update user model in Python**

Open `src/models/user.py` (or wherever your SQLAlchemy User model is defined).

Add this field to the User class:

```python
from sqlalchemy import String

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]
    # ... existing fields ...
    preferred_language: Mapped[str] = mapped_column(String(5), default="es")
```

Save the file.

- [ ] **Step 6: Commit**

```bash
git add alembic/versions/ src/models/user.py
git commit -m "feat: add preferred_language column to users table"
```

---

## Phase 1: Frontend Dependencies & Configuration

### Task 2: Install i18next Dependencies

**Files:**
- Modify: `frontend/package.json`

**Context:**
Install react-i18next and related libraries needed for translation and browser locale detection.

- [ ] **Step 1: Install packages**

Run:
```bash
cd frontend
npm install react-i18next i18next i18next-browser-languagedetector
```

Expected output: `up to date, audited X packages in Ys`

- [ ] **Step 2: Verify installation**

Run:
```bash
npm list react-i18next i18next
```

Expected output shows version numbers for both packages.

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: install react-i18next for multilanguage support"
```

---

### Task 3: Create i18next Configuration

**Files:**
- Create: `frontend/src/i18n.js`

**Context:**
i18next needs initialization with language detection, fallback language, and namespace configuration. This file is imported once at app startup.

- [ ] **Step 1: Create i18n.js file**

Create `frontend/src/i18n.js` with this content:

```javascript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import es from './locales/es.json';
import en from './locales/en.json';

const resources = {
  es: { translation: es },
  en: { translation: en },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    interpolation: {
      escapeValue: false, // React handles XSS protection
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
```

Save the file.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/i18n.js
git commit -m "feat: add i18next configuration"
```

---

### Task 4: Create Spanish Translation File

**Files:**
- Create: `frontend/src/locales/es.json`

**Context:**
Spanish translations for all UI text. This is the reference language and should have all keys needed by the app.

- [ ] **Step 1: Create locales directory**

Run:
```bash
mkdir -p frontend/src/locales
```

- [ ] **Step 2: Create es.json file**

Create `frontend/src/locales/es.json` with this content:

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
    "name": "Nombre",
    "loginError": "Correo o contraseña incorrectos",
    "registerError": "Error en el registro",
    "submit": "Enviar",
    "termsOfService": "Términos de servicio",
    "privacyPolicy": "Política de privacidad"
  },
  "common": {
    "loading": "Cargando...",
    "error": "Error",
    "success": "Éxito",
    "cancel": "Cancelar",
    "save": "Guardar",
    "delete": "Eliminar",
    "edit": "Editar",
    "close": "Cerrar",
    "submit": "Enviar"
  },
  "cv": {
    "upload": "Subir CV",
    "delete": "Eliminar CV",
    "uploading": "Subiendo CV...",
    "uploadSuccess": "CV subido correctamente",
    "uploadError": "Error al subir CV",
    "deleteSuccess": "CV eliminado correctamente",
    "deleteError": "Error al eliminar CV",
    "preview": "Vista previa del CV",
    "required": "El CV es obligatorio para continuar"
  },
  "analysis": {
    "create": "Crear análisis",
    "analyzing": "Analizando...",
    "title": "Análisis de ofertas",
    "description": "Analiza una oferta de trabajo comparándola con tu CV",
    "analyze": "Analizar",
    "history": "Historial de análisis",
    "noResults": "No hay análisis registrados",
    "error": "Error al crear análisis"
  },
  "adaptations": {
    "generate": "Generar adaptación",
    "generating": "Generando adaptación...",
    "download": "Descargar PDF",
    "title": "Adaptaciones",
    "history": "Historial de adaptaciones",
    "noResults": "No hay adaptaciones registradas",
    "error": "Error al generar adaptación"
  },
  "dashboard": {
    "welcome": "Bienvenido",
    "recentAnalyses": "Análisis recientes",
    "recentAdaptations": "Adaptaciones recientes",
    "noData": "Sin datos disponibles"
  }
}
```

Save the file.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/locales/es.json
git commit -m "feat: add Spanish translation file"
```

---

### Task 5: Create English Translation File

**Files:**
- Create: `frontend/src/locales/en.json`

**Context:**
English translations with identical key structure to Spanish file. All keys from es.json must exist here.

- [ ] **Step 1: Create en.json file**

Create `frontend/src/locales/en.json` with this content:

```json
{
  "nav": {
    "home": "Home",
    "dashboard": "Dashboard",
    "profile": "Profile",
    "logout": "Logout",
    "language": "Language"
  },
  "auth": {
    "login": "Sign In",
    "register": "Sign Up",
    "email": "Email",
    "password": "Password",
    "confirmPassword": "Confirm Password",
    "name": "Name",
    "loginError": "Invalid email or password",
    "registerError": "Registration failed",
    "submit": "Submit",
    "termsOfService": "Terms of Service",
    "privacyPolicy": "Privacy Policy"
  },
  "common": {
    "loading": "Loading...",
    "error": "Error",
    "success": "Success",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete",
    "edit": "Edit",
    "close": "Close",
    "submit": "Submit"
  },
  "cv": {
    "upload": "Upload CV",
    "delete": "Delete CV",
    "uploading": "Uploading CV...",
    "uploadSuccess": "CV uploaded successfully",
    "uploadError": "Error uploading CV",
    "deleteSuccess": "CV deleted successfully",
    "deleteError": "Error deleting CV",
    "preview": "CV Preview",
    "required": "CV is required to continue"
  },
  "analysis": {
    "create": "Create Analysis",
    "analyzing": "Analyzing...",
    "title": "Offer Analysis",
    "description": "Analyze a job offer by comparing it with your CV",
    "analyze": "Analyze",
    "history": "Analysis History",
    "noResults": "No analyses found",
    "error": "Error creating analysis"
  },
  "adaptations": {
    "generate": "Generate Adaptation",
    "generating": "Generating adaptation...",
    "download": "Download PDF",
    "title": "Adaptations",
    "history": "Adaptation History",
    "noResults": "No adaptations found",
    "error": "Error generating adaptation"
  },
  "dashboard": {
    "welcome": "Welcome",
    "recentAnalyses": "Recent Analyses",
    "recentAdaptations": "Recent Adaptations",
    "noData": "No data available"
  }
}
```

Save the file.

- [ ] **Step 2: Verify key consistency**

Run (in project root, or create a simple Node script):
```javascript
const es = require('./frontend/src/locales/es.json');
const en = require('./frontend/src/locales/en.json');

const esKeys = new Set(JSON.stringify(es).match(/"[a-zA-Z_]+"\s*:/g));
const enKeys = new Set(JSON.stringify(en).match(/"[a-zA-Z_]+"\s*:/g));

if (esKeys.size !== enKeys.size) {
  console.error('Key mismatch!');
  console.error('In ES but not EN:', [...esKeys].filter(k => !enKeys.has(k)));
  console.error('In EN but not ES:', [...enKeys].filter(k => !esKeys.has(k)));
} else {
  console.log('✓ All keys match');
}
```

Expected output: `✓ All keys match`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/locales/en.json
git commit -m "feat: add English translation file"
```

---

## Phase 2: Locale Service & State Management

### Task 6: Create Locale Service

**Files:**
- Create: `frontend/src/services/localeService.js`

**Context:**
Centralized business logic for locale detection, initialization, and syncing to the database. This service encapsulates all locale-related operations.

- [ ] **Step 1: Create services directory if needed**

Run:
```bash
mkdir -p frontend/src/services
```

(It may already exist; if so, just proceed.)

- [ ] **Step 2: Create localeService.js**

Create `frontend/src/services/localeService.js` with this content:

```javascript
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
```

Save the file.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/localeService.js
git commit -m "feat: add locale service with browser detection and sync logic"
```

---

### Task 7: Create useLocale Hook

**Files:**
- Create: `frontend/src/hooks/useLocale.js`

**Context:**
A custom hook that provides clean access to translation function and locale state from any component. Wraps useTranslation and Zustand store.

- [ ] **Step 1: Create hooks directory if needed**

Run:
```bash
mkdir -p frontend/src/hooks
```

- [ ] **Step 2: Create useLocale.js**

Create `frontend/src/hooks/useLocale.js` with this content:

```javascript
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
```

Save the file.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useLocale.js
git commit -m "feat: add useLocale hook for component access to translations"
```

---

### Task 8: Add Locale Slice to Zustand Store

**Files:**
- Modify: `frontend/src/stores/globalStore.js` (around line 8, in the create function)

**Context:**
Add a new locale slice to the global Zustand store to manage language state centrally. Insert after the auth slice.

- [ ] **Step 1: Open globalStore.js**

Open `frontend/src/stores/globalStore.js` and locate the `create((set, get) => ({` line (around line 8).

- [ ] **Step 2: Add locale slice**

After the `authActions` object (around line 126), add this locale slice:

```javascript
  // ===== LOCALE SLICE =====
  locale: {
    current: 'es',
    available: ['es', 'en'],
    isSyncing: false,
    syncError: null,
    isInitialized: false,
  },

  localeActions: {
    setLocale: (locale) => set((state) => ({
      locale: { ...state.locale, current: locale }
    })),

    setSyncing: (isSyncing) => set((state) => ({
      locale: { ...state.locale, isSyncing }
    })),

    setSyncError: (error) => set((state) => ({
      locale: { ...state.locale, syncError: error }
    })),

    setInitialized: (initialized) => set((state) => ({
      locale: { ...state.locale, isInitialized: initialized }
    })),
  },
```

Save the file.

- [ ] **Step 3: Verify syntax**

Run:
```bash
cd frontend
npm run dev
```

The app should start without errors. Check browser console for any errors.

Expected output: Dev server starts on `http://localhost:5173` (or similar) without errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/globalStore.js
git commit -m "feat: add locale slice to global store"
```

---

## Phase 3: App Initialization

### Task 9: Initialize Locale on App Startup

**Files:**
- Modify: `frontend/src/App.jsx`

**Context:**
Call `initLocale()` in a useEffect hook when the app first loads. This detects the browser language and sets up i18next.

- [ ] **Step 1: Open App.jsx**

Open `frontend/src/App.jsx`.

- [ ] **Step 2: Import required modules**

At the top of the file, add these imports:

```javascript
import { useEffect } from 'react';
import { initLocale } from './services/localeService';
import useStore from './stores/globalStore';
```

- [ ] **Step 3: Add initialization effect**

Inside the App component (before the return statement), add this effect:

```javascript
  useEffect(() => {
    // Initialize locale on first app load
    const initializeLocale = async () => {
      const { auth, localeActions, profile } = useStore.getState();
      
      // If user is authenticated, pass their profile
      const userProfile = profile.data;
      
      try {
        await initLocale(userProfile);
        localeActions.setInitialized(true);
      } catch (error) {
        console.error('Failed to initialize locale:', error);
      }
    };
    
    initializeLocale();
  }, []);
```

Save the file.

- [ ] **Step 4: Test in browser**

Run the dev server (if not already running):
```bash
npm run dev
```

Open the app in browser at `http://localhost:5173`.

Expected: App loads without errors. Check browser console for any errors. Locale should be initialized.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: initialize locale on app startup"
```

---

## Phase 4: Navbar Integration

### Task 10: Add Language Selector to Navbar

**Files:**
- Modify: `frontend/src/shared/components/Navbar.jsx`

**Context:**
Add ES/EN language selector buttons to the Navbar. Buttons should call changeLocale() when clicked and show the current language.

- [ ] **Step 1: Open Navbar.jsx**

Open `frontend/src/shared/components/Navbar.jsx`.

- [ ] **Step 2: Add imports**

At the top of the file, add:

```javascript
import { useLocale } from '../../hooks/useLocale';
```

- [ ] **Step 3: Get locale state in component**

Inside the Navbar component (before the return statement), add:

```javascript
  const { locale, changeLocale, isSyncing } = useLocale();
```

- [ ] **Step 4: Add language selector UI**

Find the navbar's JSX return statement. Add a language selector section near the right side of the navbar (alongside logout, profile, etc.). Example placement:

```jsx
<nav className="navbar">
  {/* Existing navbar content */}
  
  <div className="flex items-center gap-2">
    {/* Language Selector */}
    <div className="flex gap-1 border-l pl-4">
      <button
        onClick={() => changeLocale('es')}
        className={`px-3 py-1 rounded text-sm font-medium transition ${
          locale === 'es'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
        disabled={isSyncing}
      >
        ES
      </button>
      <button
        onClick={() => changeLocale('en')}
        className={`px-3 py-1 rounded text-sm font-medium transition ${
          locale === 'en'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
        disabled={isSyncing}
      >
        EN
      </button>
      {isSyncing && <span className="text-xs text-gray-500 ml-2">Syncing...</span>}
    </div>
    
    {/* Existing navbar items (logout, profile, etc.) */}
  </div>
</nav>
```

Adjust CSS classes as needed to match your existing Navbar styling (Tailwind, CSS modules, etc.).

Save the file.

- [ ] **Step 2: Test in browser**

Refresh the app and look for the ES/EN buttons in the Navbar. Click them to verify language changes.

Expected:
- Buttons appear in navbar
- Clicking ES/EN changes the page language
- Current language button is highlighted (blue)
- Other button is gray

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/components/Navbar.jsx
git commit -m "feat: add language selector to Navbar"
```

---

## Phase 5: Component Migration (Incremental)

### Task 11: Migrate Auth Components to Use Translations

**Files:**
- Modify: `frontend/src/features/auth/pages/LoginPage.jsx`
- Modify: `frontend/src/features/auth/pages/RegisterPage.jsx`
- Modify: `frontend/src/features/auth/components/LoginForm.jsx`
- Modify: `frontend/src/features/auth/components/RegisterForm.jsx`

**Context:**
Replace hardcoded strings with `t()` function calls. This makes the auth flow translatable.

- [ ] **Step 1: Open LoginPage.jsx**

Open `frontend/src/features/auth/pages/LoginPage.jsx`.

- [ ] **Step 2: Add import**

At the top, add:

```javascript
import { useLocale } from '../../../hooks/useLocale';
```

- [ ] **Step 3: Get translation function**

Inside the component, add:

```javascript
  const { t } = useLocale();
```

- [ ] **Step 4: Replace hardcoded strings**

Find all text strings and replace with `t()` calls. Examples:

```jsx
// Before
<h1>Sign In</h1>
<input placeholder="Email" />
<button>Login</button>

// After
<h1>{t('auth.login')}</h1>
<input placeholder={t('auth.email')} />
<button>{t('auth.submit')}</button>
```

Do the same for any error messages, labels, etc. Check the es.json file for available keys.

Save the file.

- [ ] **Step 5: Repeat for RegisterPage.jsx**

Open `frontend/src/features/auth/pages/RegisterPage.jsx` and repeat steps 2-4.

- [ ] **Step 6: Repeat for LoginForm.jsx**

Open `frontend/src/features/auth/components/LoginForm.jsx` and repeat steps 2-4.

- [ ] **Step 7: Repeat for RegisterForm.jsx**

Open `frontend/src/features/auth/components/RegisterForm.jsx` and repeat steps 2-4.

- [ ] **Step 8: Test in browser**

Refresh the app. Navigate to Login/Register pages. Verify:
- Text appears correctly in Spanish
- Changing language in Navbar updates the text on these pages
- Form still works correctly

Expected: No errors, text updates when language changes.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/features/auth/pages/LoginPage.jsx frontend/src/features/auth/pages/RegisterPage.jsx frontend/src/features/auth/components/LoginForm.jsx frontend/src/features/auth/components/RegisterForm.jsx
git commit -m "feat: migrate auth components to use translations"
```

---

### Task 12: Migrate Landing Page

**Files:**
- Modify: `frontend/src/features/landing/pages/LandingPage.jsx`

**Context:**
Translate landing page content.

- [ ] **Step 1: Open LandingPage.jsx**

Open `frontend/src/features/landing/pages/LandingPage.jsx`.

- [ ] **Step 2: Add import and get t()**

```javascript
import { useLocale } from '../../../hooks/useLocale';

export function LandingPage() {
  const { t } = useLocale();
  // ... rest of component
}
```

- [ ] **Step 3: Replace hardcoded strings**

Find all text and replace with `t()` calls. Use keys from es.json (nav.*, common.*, analysis.*, cv.*, adaptations.*).

Save the file.

- [ ] **Step 4: Test in browser**

Navigate to landing page. Verify text is translated and updates with language change.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/landing/pages/LandingPage.jsx
git commit -m "feat: migrate landing page to use translations"
```

---

### Task 13: Migrate Shared Components (Layout, Footer, Modal)

**Files:**
- Modify: `frontend/src/shared/components/Layout.jsx`
- Modify: `frontend/src/shared/components/Footer.jsx`
- Modify: `frontend/src/shared/components/Modal.jsx`
- Modify: `frontend/src/shared/components/Toast.jsx`

**Context:**
Shared components need translations for common UI elements.

- [ ] **Step 1: Layout.jsx**

Open the file, add `useLocale` import, get `t()`, and replace strings like "Close", "Cancel", etc. with `t('common.close')`, etc.

Save.

- [ ] **Step 2: Footer.jsx**

Same process as Layout.jsx.

Save.

- [ ] **Step 3: Modal.jsx**

Replace button labels and any static text.

Save.

- [ ] **Step 4: Toast.jsx**

Replace any static messages.

Save.

- [ ] **Step 5: Test in browser**

Trigger toasts and modals. Verify text is translated.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/shared/components/Layout.jsx frontend/src/shared/components/Footer.jsx frontend/src/shared/components/Modal.jsx frontend/src/shared/components/Toast.jsx
git commit -m "feat: migrate shared components to use translations"
```

---

### Task 14: Migrate Dashboard and Main Pages

**Files:**
- Modify: `frontend/src/features/dashboard/pages/DashboardPage.jsx`
- Modify: `frontend/src/features/cv/pages/CVPage.jsx`
- Modify: `frontend/src/features/analysis/pages/AnalysisPage.jsx`
- Modify: `frontend/src/features/analysis/pages/HistoryPage.jsx`
- Modify: `frontend/src/features/analysis/pages/ResultPage.jsx`
- Modify: `frontend/src/features/adaptations/pages/AdaptationPage.jsx`
- Modify: `frontend/src/features/adaptations/pages/AdaptationDetailPage.jsx`
- Modify: `frontend/src/features/adaptations/pages/AdaptationsHistoryPage.jsx`
- Modify: `frontend/src/features/profile/pages/ProfilePage.jsx`

**Context:**
Migrate all remaining pages to use translations. Focus on UI text (labels, button text, titles) but NOT on user-generated content or sensitive data (CV content, job offer details, analysis results).

- [ ] **Step 1-9: For each file**

For each file listed above:
1. Open the file
2. Add: `import { useLocale } from '../../../hooks/useLocale';` (adjust path)
3. Inside component: `const { t } = useLocale();`
4. Replace hardcoded UI strings with `t()` calls
5. Save

Examples of strings to replace:
- Button labels: "Analyze", "Generate", "Download", "Delete", "Edit"
- Form labels: "Email", "Name", "Password"
- Titles: "Analysis History", "Dashboard", "Profile"
- Error/success messages

Examples of strings to NOT replace:
- CV preview text (user's actual CV)
- Job offer details from API
- Analysis results or explanations
- Names, emails, company info from backend

- [ ] **Step 10: Test all pages**

Refresh the app. Navigate through all pages. Verify:
- UI text is in the selected language
- Changing language updates all pages
- No errors in console
- User content (CV, job offers, etc.) is NOT translated

- [ ] **Step 11: Commit**

```bash
git add frontend/src/features/dashboard/pages/DashboardPage.jsx frontend/src/features/cv/pages/CVPage.jsx frontend/src/features/analysis/pages/AnalysisPage.jsx frontend/src/features/analysis/pages/HistoryPage.jsx frontend/src/features/analysis/pages/ResultPage.jsx frontend/src/features/adaptations/pages/AdaptationPage.jsx frontend/src/features/adaptations/pages/AdaptationDetailPage.jsx frontend/src/features/adaptations/pages/AdaptationsHistoryPage.jsx frontend/src/features/profile/pages/ProfilePage.jsx
git commit -m "feat: migrate all pages to use translations"
```

---

### Task 15: Migrate Components (Second Pass)

**Files:**
- Modify: `frontend/src/features/cv/components/CVUpload.jsx`
- Modify: `frontend/src/features/cv/components/CVPreview.jsx`
- Modify: `frontend/src/features/analysis/components/AnalysisForm.jsx`
- Modify: `frontend/src/features/analysis/components/AnalysisListItem.jsx`
- Modify: `frontend/src/features/analysis/components/ResultCard.jsx`
- Modify: `frontend/src/features/adaptations/components/AdaptationPreview.jsx`
- Modify: `frontend/src/features/adaptations/components/CVPreviewHTML.jsx`
- Modify: `frontend/src/features/adaptations/components/PDFDownloadButton.jsx`
- Modify: `frontend/src/shared/components/Sidebar.jsx`
- Modify: `frontend/src/shared/components/CardItem.jsx`
- Modify: `frontend/src/shared/components/Spinner.jsx`
- Modify: `frontend/src/shared/components/ProtectedRoute.jsx`
- Modify: `frontend/src/shared/components/CVRequiredRoute.jsx`

**Context:**
Migrate remaining components using the same pattern.

- [ ] **Step 1-13: For each file**

Repeat the process from Task 14:
1. Open file
2. Import useLocale
3. Call `const { t } = useLocale();`
4. Replace UI strings with `t()` calls
5. Save

- [ ] **Step 14: Full app test**

Refresh and test the entire app:
- Click through all pages
- Change language multiple times
- Verify all UI text updates
- Check console for errors

Expected: No errors, all UI text translated, language changes work smoothly.

- [ ] **Step 15: Commit**

```bash
git add frontend/src/features/cv/components/CVUpload.jsx frontend/src/features/cv/components/CVPreview.jsx frontend/src/features/analysis/components/AnalysisForm.jsx frontend/src/features/analysis/components/AnalysisListItem.jsx frontend/src/features/analysis/components/ResultCard.jsx frontend/src/features/adaptations/components/AdaptationPreview.jsx frontend/src/features/adaptations/components/CVPreviewHTML.jsx frontend/src/features/adaptations/components/PDFDownloadButton.jsx frontend/src/shared/components/Sidebar.jsx frontend/src/shared/components/CardItem.jsx frontend/src/shared/components/Spinner.jsx frontend/src/shared/components/ProtectedRoute.jsx frontend/src/shared/components/CVRequiredRoute.jsx
git commit -m "feat: migrate all components to use translations"
```

---

## Phase 6: Testing

### Task 16: Write Unit Tests for localeService

**Files:**
- Create: `tests/frontend/services/localeService.test.js`

**Context:**
Test the locale service functions: detection, initialization, and sync logic.

- [ ] **Step 1: Create test directory**

Run:
```bash
mkdir -p tests/frontend/services
```

- [ ] **Step 2: Create localeService.test.js**

Create `tests/frontend/services/localeService.test.js` with:

```javascript
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
```

Save the file.

- [ ] **Step 3: Run tests**

Run:
```bash
npm test tests/frontend/services/localeService.test.js
```

Expected output: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/frontend/services/localeService.test.js
git commit -m "test: add unit tests for localeService"
```

---

### Task 17: Write Unit Tests for useLocale Hook

**Files:**
- Create: `tests/frontend/hooks/useLocale.test.js`

**Context:**
Test the useLocale hook to ensure it provides correct values.

- [ ] **Step 1: Create test directory**

Run:
```bash
mkdir -p tests/frontend/hooks
```

- [ ] **Step 2: Create useLocale.test.js**

Create `tests/frontend/hooks/useLocale.test.js` with:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocale } from '../../../frontend/src/hooks/useLocale';

// Mock the store and services
vi.mock('../../../frontend/src/stores/globalStore', () => ({
  default: vi.fn(() => ({
    locale: {
      current: 'es',
      available: ['es', 'en'],
      isSyncing: false,
      syncError: null,
    },
    localeActions: {
      setLocale: vi.fn(),
      setSyncing: vi.fn(),
      setSyncError: vi.fn(),
    },
    auth: { token: null },
  })),
}));

vi.mock('../../../frontend/src/services/localeService', () => ({
  changeLocale: vi.fn(),
}));

describe('useLocale', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return translation function and locale state', () => {
    const { result } = renderHook(() => useLocale());

    expect(result.current.t).toBeDefined();
    expect(result.current.locale).toBe('es');
    expect(result.current.available).toEqual(['es', 'en']);
    expect(result.current.isSyncing).toBe(false);
    expect(result.current.syncError).toBeNull();
  });

  it('should have a changeLocale function', () => {
    const { result } = renderHook(() => useLocale());
    expect(typeof result.current.changeLocale).toBe('function');
  });

  it('should have i18n instance', () => {
    const { result } = renderHook(() => useLocale());
    expect(result.current.i18n).toBeDefined();
  });
});
```

Save the file.

- [ ] **Step 3: Run tests**

Run:
```bash
npm test tests/frontend/hooks/useLocale.test.js
```

Expected output: Tests pass (or may skip due to mock setup, which is OK).

- [ ] **Step 4: Commit**

```bash
git add tests/frontend/hooks/useLocale.test.js
git commit -m "test: add unit tests for useLocale hook"
```

---

### Task 18: Validate Translation File Consistency

**Files:**
- Create: `tests/frontend/locales/translations.test.js`

**Context:**
Verify that all keys exist in both language files and no extra keys are present.

- [ ] **Step 1: Create test directory**

Run:
```bash
mkdir -p tests/frontend/locales
```

- [ ] **Step 2: Create translations.test.js**

Create `tests/frontend/locales/translations.test.js` with:

```javascript
import { describe, it, expect } from 'vitest';
import es from '../../../frontend/src/locales/es.json';
import en from '../../../frontend/src/locales/en.json';

describe('Translations', () => {
  function getKeys(obj, prefix = '') {
    let keys = [];
    for (const key in obj) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      if (typeof obj[key] === 'object' && obj[key] !== null) {
        keys = keys.concat(getKeys(obj[key], fullKey));
      } else {
        keys.push(fullKey);
      }
    }
    return keys;
  }

  it('should have same keys in both language files', () => {
    const esKeys = new Set(getKeys(es));
    const enKeys = new Set(getKeys(en));

    const missingInEn = [...esKeys].filter(k => !enKeys.has(k));
    const missingInEs = [...enKeys].filter(k => !esKeys.has(k));

    expect(missingInEn).toHaveLength(0, `Keys in ES but not EN: ${missingInEn.join(', ')}`);
    expect(missingInEs).toHaveLength(0, `Keys in EN but not ES: ${missingInEs.join(', ')}`);
  });

  it('should not have empty translation values', () => {
    const esKeys = getKeys(es);
    const enKeys = getKeys(en);

    esKeys.forEach(key => {
      const value = key.split('.').reduce((obj, k) => obj[k], es);
      expect(value).toBeTruthy(`ES translation empty for key: ${key}`);
    });

    enKeys.forEach(key => {
      const value = key.split('.').reduce((obj, k) => obj[k], en);
      expect(value).toBeTruthy(`EN translation empty for key: ${key}`);
    });
  });
});
```

Save the file.

- [ ] **Step 3: Run tests**

Run:
```bash
npm test tests/frontend/locales/translations.test.js
```

Expected output: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/frontend/locales/translations.test.js
git commit -m "test: add translation consistency validation"
```

---

### Task 19: Manual Testing Checklist

**Files:** (None)

**Context:**
Perform manual testing of the multilanguage feature across the app.

- [ ] **Step 1: Test browser locale detection**

1. Clear browser localStorage: `localStorage.clear()` in console
2. Refresh the app
3. Check that the language matches your browser's language preference
4. If browser is EN, page should load in EN; if browser is ES, page should load in ES

Expected: Language auto-detects correctly.

- [ ] **Step 2: Test language switching**

1. Click the ES button in Navbar
2. Verify entire UI changes to Spanish
3. Click the EN button
4. Verify entire UI changes to English
5. Repeat 5 times to ensure reliability

Expected: No errors, instant language switching.

- [ ] **Step 3: Test localStorage persistence**

1. Refresh the browser
2. Verify the language persists (stays on the language you selected)

Expected: Persists across refresh.

- [ ] **Step 4: Test authentication flow**

1. If not logged in, log in
2. Check that language preference is still maintained
3. (If database is set up) Log out, log in as a different user, verify each user's preference is respected

Expected: Language persists through auth flow.

- [ ] **Step 5: Test all pages**

Navigate to each page:
- Landing page
- Login/Register
- Dashboard
- CV page
- Analysis page
- Analysis history
- Adaptations page
- Adaptations history
- Profile page

For each page:
1. Verify UI text is in the selected language
2. Change language and verify UI updates
3. Verify user-generated content (CV, offers, results) is NOT translated

Expected: All pages translate correctly, user content unchanged.

- [ ] **Step 6: Test edge cases**

1. Open app in browser with unsupported language (e.g., French) → should default to Spanish
2. Manually set localStorage to invalid locale → should fallback to Spanish
3. Change language rapidly (click ES, EN, ES, EN) → no errors
4. Change language on form with errors → language updates, errors persist

Expected: Graceful handling of edge cases.

- [ ] **Step 7: Test on different devices**

If possible:
1. Test on mobile browser
2. Test on tablet
3. Verify language selector fits and works on small screens

Expected: Works on all screen sizes.

- [ ] **Step 8: Document test results**

Create `tests/MANUAL_TEST_RESULTS.md` with:

```markdown
# Multilanguage Feature - Manual Test Results

**Date:** [Today's date]
**Tester:** [Your name]

## Test Results

- [x] Browser locale detection works
- [x] Language switching is instant
- [x] localStorage persistence works
- [x] Auth flow preserves language
- [x] All pages display correctly in both languages
- [x] User content is not translated
- [x] Edge cases handled gracefully
- [x] Works on mobile/tablet

## Issues Found

None

## Notes

All manual tests passed successfully.
```

Save the file.

- [ ] **Step 9: Commit**

```bash
git add tests/MANUAL_TEST_RESULTS.md
git commit -m "test: complete manual testing of multilanguage feature"
```

---

## Phase 7: Finalization

### Task 20: Final Integration Test

**Files:** (None)

**Context:**
Perform a comprehensive integration test to verify all components work together.

- [ ] **Step 1: Full app restart**

1. Stop the dev server (Ctrl+C)
2. Clear browser cache and localStorage
3. Restart the dev server: `npm run dev`
4. Open the app in a fresh browser tab

Expected: App loads, locale initializes correctly, no errors in console.

- [ ] **Step 2: Test full user journey**

1. Land on landing page in Spanish (if browser is Spanish)
2. Click login button
3. Log in successfully
4. Navigate to dashboard
5. Change language to English
6. Navigate to CV page, upload CV
7. Navigate to analysis, create analysis
8. Change language back to Spanish
9. Navigate to adaptations
10. Log out
11. Verify language persists on landing page

Expected: Entire flow works without errors, language switches smoothly.

- [ ] **Step 3: Check browser console**

Open developer tools (F12) and check the Console tab.

Expected: No errors, no warnings related to i18n or translations.

- [ ] **Step 4: Run all tests**

Run:
```bash
npm test
```

Expected: All tests pass (or have no multilanguage-related failures).

- [ ] **Step 5: Build for production**

Run:
```bash
npm run build
```

Expected: Build succeeds without errors.

- [ ] **Step 6: Commit final integration**

```bash
git add -A
git commit -m "feat: complete multilanguage implementation with full testing"
```

---

## Summary

**Total Tasks:** 20 (organized in 7 phases)

**Phase 0 (Backend):** 1 task - Database migration
**Phase 1 (Frontend Setup):** 4 tasks - Dependencies, i18next config, translation files
**Phase 2 (Services):** 3 tasks - Locale service, useLocale hook, Zustand slice
**Phase 3 (Initialization):** 1 task - App startup
**Phase 4 (Navbar):** 1 task - Language selector
**Phase 5 (Component Migration):** 5 tasks - Auth, landing, shared, main pages, sub-components
**Phase 6 (Testing):** 4 tasks - Unit tests, translation validation, manual testing
**Phase 7 (Finalization):** 1 task - Integration test

**Estimated Timeline:** 2-3 days with thorough testing

---

**End of Implementation Plan**
