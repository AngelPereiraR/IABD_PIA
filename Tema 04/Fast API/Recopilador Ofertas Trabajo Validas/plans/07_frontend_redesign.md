# Frontend Redesign Specification
**Date:** 2026-04-20  
**Status:** Approved  
**Project:** Recopilador Inteligente de Ofertas (Dual-Mode Platform)

---

## Executive Summary

Redesign React frontend to support new FastAPI capabilities: JWT authentication, CV management, job offer analysis (DeepSeek), and adaptive CV generation with PDF download. Architecture uses feature-based modules, centralized Zustand state, and responsive sidebar navigation.

**Key Outcomes:**
- Single CV lifecycle management
- Decoupled analysis → history → optional adaptation workflow
- Immediate HTML preview before PDF generation
- Persistent authentication with auto-logout on token expiry
- Mobile-responsive design

---

## 1. Architecture Overview

### 1.1 Tech Stack
- **UI Framework:** React 18 + Vite
- **Routing:** React Router v6
- **State Management:** Zustand (single global store)
- **HTTP Client:** Axios with interceptor for Bearer token
- **Form Validation:** React Hook Form + Zod
- **UI Library:** Tailwind CSS
- **Data Fetching:** React Query (TanStack Query) for analysis/adaptation caching
- **Build:** Vite dev server + production build

### 1.2 Folder Structure (Feature-Based Hybrid)

```
src/
├── features/
│   ├── auth/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── GoogleCallbackPage.jsx
│   │   ├── components/
│   │   │   ├── LoginForm.jsx
│   │   │   └── RegisterForm.jsx
│   │   └── hooks/
│   │       ├── useLogin.js
│   │       └── useRegister.js
│   ├── cv/
│   │   ├── pages/
│   │   │   └── CVPage.jsx
│   │   ├── components/
│   │   │   ├── CVUpload.jsx
│   │   │   └── CVPreview.jsx
│   │   └── hooks/
│   │       └── useCVUpload.js
│   ├── analysis/
│   │   ├── pages/
│   │   │   ├── AnalysisPage.jsx
│   │   │   ├── ResultPage.jsx
│   │   │   └── HistoryPage.jsx
│   │   ├── components/
│   │   │   ├── AnalysisForm.jsx
│   │   │   ├── ResultCard.jsx
│   │   │   └── AnalysisListItem.jsx
│   │   └── hooks/
│   │       └── useAnalysis.js
│   ├── adaptations/
│   │   ├── pages/
│   │   │   └── AdaptationPage.jsx
│   │   ├── components/
│   │   │   ├── CVPreviewHTML.jsx
│   │   │   └── PDFDownloadButton.jsx
│   │   └── hooks/
│   │       └── useAdaptation.js
│   └── landing/
│       ├── pages/
│       │   └── LandingPage.jsx
│       └── components/
│           ├── Hero.jsx
│           ├── Features.jsx
│           └── CTA.jsx
├── shared/
│   ├── components/
│   │   ├── Layout.jsx
│   │   ├── Sidebar.jsx
│   │   ├── Navbar.jsx
│   │   └── ProtectedRoute.jsx
│   ├── ui/
│   │   ├── Button.jsx
│   │   ├── Input.jsx
│   │   ├── Modal.jsx
│   │   ├── Toast.jsx
│   │   └── Spinner.jsx
│   └── hooks/
│       ├── useAuth.js
│       └── useToast.js
├── stores/
│   ├── globalStore.js (Zustand store with slices)
│   └── types.js (TypeScript-like types/validations)
├── services/
│   ├── apiClient.js (Axios instance with interceptors)
│   ├── authService.js
│   ├── cvService.js
│   ├── analysisService.js
│   └── adaptationService.js
├── utils/
│   ├── validators.js
│   ├── formatters.js
│   └── constants.js
├── App.jsx
└── main.jsx
```

---

## 2. State Management (Zustand)

### 2.1 Single Global Store

**File:** `src/stores/globalStore.js`

```javascript
// Struktur logiska (pseudo-code)
create((set) => ({
  // Auth slice
  auth: {
    user: null,
    token: null,
    isLoading: false,
    error: null,
  },
  authActions: {
    setUser: (user) => set(...),
    setToken: (token) => set(...),
    login: async (email, password) => { ... },
    registerUser: async (email, password, name) => { ... },
    googleCallback: async (code) => { ... },
    logout: () => set(...),
  },

  // CV slice
  cv: {
    currentCV: null,
    isUploading: false,
    error: null,
  },
  cvActions: {
    uploadCV: async (file) => { ... },
    setCurrentCV: (cv) => set(...),
    deleteCV: async () => { ... },
  },

  // Analysis slice
  analysis: {
    analyses: [],
    currentAnalysis: null,
    isAnalyzing: false,
    error: null,
  },
  analysisActions: {
    createAnalysis: async (input) => { ... },
    setCurrentAnalysis: (analysis) => set(...),
    addAnalysisToHistory: (analysis) => set(...),
    loadAnalysisHistory: async (limit, offset) => { ... },
  },

  // Adaptations slice
  adaptations: {
    adaptations: [],
    currentAdaptation: null,
    isGenerating: false,
    error: null,
  },
  adaptationActions: {
    createAdaptation: async (analysisId) => { ... },
    setCurrentAdaptation: (adaptation) => set(...),
    loadAdaptationHistory: async (limit, offset) => { ... },
  },
}))
```

### 2.2 Store Usage Pattern

Components access store via hooks:

```javascript
import useStore from '@/stores/globalStore';

function MyComponent() {
  const { user, token } = useStore((state) => state.auth);
  const { login } = useStore((state) => state.authActions);
  
  // Use user, token, login...
}
```

---

## 3. Routing and Navigation

### 3.1 Route Structure

```
/ (public)
├── (Landing page - no auth required)

/auth (public)
├── /login
├── /register
└── /google-callback

/dashboard/* (protected - requires auth + CV)
├── /cv (CV management)
├── /analysis (create new analysis)
├── /analysis/:id (view result)
├── /analysis/history (paginated list)
└── /adaptations/:analysisId (preview + download)
```

### 3.2 Route Protection

**Guards:**

1. **ProtectedRoute** - Redirects to login if no token
2. **CVRequiredRoute** - Redirects to /dashboard/cv if CV not uploaded

**Implementation:**

```javascript
function ProtectedRoute({ children }) {
  const { user, token } = useStore(state => state.auth);
  if (!token) return <Navigate to="/auth/login" />;
  return children;
}

function CVRequiredRoute({ children }) {
  const { currentCV } = useStore(state => state.cv);
  if (!currentCV) return <Navigate to="/dashboard/cv" />;
  return children;
}

// Usage
<Routes>
  <Route path="/dashboard/analysis" element={
    <ProtectedRoute>
      <CVRequiredRoute>
        <AnalysisPage />
      </CVRequiredRoute>
    </ProtectedRoute>
  } />
</Routes>
```

---

## 4. Data Flow and Services

### 4.1 API Client

**File:** `src/services/apiClient.js`

```javascript
// Axios instance with:
// - BASE_URL from env
// - Bearer token interceptor
// - Error handler (401 → logout)
// - Request/response transformation

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:7860',
});

// Request interceptor: add Authorization header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, logout
      useStore.getState().authActions.logout();
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);
```

### 4.2 Service Layer

Each domain has a service module:

**authService.js:**
```javascript
export const authService = {
  register: (email, password, name) => 
    apiClient.post('/auth/register', { email, password, name }),
  
  login: (email, password) =>
    apiClient.post('/auth/login', { email, password }),
  
  googleCallback: (code) =>
    apiClient.post('/auth/google-callback', { code }),
  
  getMe: () =>
    apiClient.get('/auth/me'),
};
```

Similar for cvService, analysisService, adaptationService.

### 4.3 Data Flow Example (Analysis Creation)

```
User fills AnalysisForm (URL or text)
  ↓
useAnalysis hook validates input (zod)
  ↓
Call store.analysisActions.createAnalysis(input)
  ↓
Store calls analysisService.createAnalysis(input)
  ↓
Service makes POST /api/analysis/create
  ↓
Backend returns { id, score, is_valid, title, company, ... }
  ↓
Store updates state.analysis.currentAnalysis
  ↓
ResultPage component re-renders with result
  ↓
User can "Generate CV Adaptation" if is_valid=true
```

---

## 5. Component Architecture

### 5.1 Feature Components

**CVPage:**
- Two sections:
  - CVUpload (drag-drop, file validation, progress)
  - CVPreview (shows current CV info, delete button)
- Handles: upload, preview, deletion
- Error: size, format, network

**AnalysisPage:**
- AnalysisForm (tabs: URL vs Text input)
- Validation: URL format, text length
- Loading state: spinner, disabled button
- Success: redirect to ResultPage

**ResultPage:**
- ResultCard displays: score (0-100), is_valid (T/F), extracted title/company/salary/benefits
- If is_valid=true: "Generate CV Adaptation" button
- Breadcrumb or back button

**HistoryPage:**
- Paginated list of analyses (limit 10, offset controls)
- AnalysisListItem: score badge, title, company, action buttons (view detail, generate adaptation)
- No results message if empty

**AdaptationPage:**
- Split view or sequential:
  1. CVPreviewHTML (renders HTML preview of adapted CV)
  2. "Download PDF" button triggers generation
  3. Loading spinner during PDF generation
  4. After done: direct download or link

### 5.2 Shared Components

**Layout:**
- Wrapper for authenticated pages
- Contains: Sidebar, Navbar, main content area
- Responsive: sidebar collapses on mobile

**Sidebar:**
- Nav items (with icons):
  - Dashboard
  - My CV
  - Analysis
  - My Adaptations
- User info (email, logout button)
- CV status indicator (✓ CV uploaded / ✗ No CV)

**Navbar:**
- Logo/brand
- User profile dropdown
- Logout

---

## 6. Validation and Error Handling

### 6.1 Input Validation (Frontend)

**Auth:**
```javascript
const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
});
```

**Analysis:**
```javascript
// URL: must be http/https
// Text: 50-5000 characters
```

**CV Upload:**
```javascript
// File type: application/pdf
// Size: < 10MB
```

### 6.2 Error Handling

**HTTP Errors:**
- 400: Show validation error message in form
- 401: Auto-logout, redirect to login
- 404: Show "Not found" message
- 429: Show "Too many requests, please wait"
- 500: Show "Server error, try again later"

**UI Pattern:**
```javascript
// Each async action sets: isLoading, error
// Component shows:
// - Loading: disable inputs, show spinner
// - Error: toast notification (red)
// - Success: toast notification (green), redirect if applicable
```

---

## 7. Session Management

### 7.1 Token Persistence

```javascript
// On successful login:
localStorage.setItem('token', response.token);
localStorage.setItem('user', JSON.stringify(response.user));

// On app mount:
useEffect(() => {
  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user'));
  if (token && user) {
    store.setUser(user);
    store.setToken(token);
  }
}, []);

// On logout:
localStorage.removeItem('token');
localStorage.removeItem('user');
```

### 7.2 Token Expiry

- API client interceptor catches 401
- Auto-logs out user
- Redirects to login page

---

## 8. Performance and Optimization

### 8.1 Caching Strategy

**React Query:**
- Cache analysis results (stale time: 5 min)
- Cache adaptation previews (stale time: 10 min)
- Avoid duplicate requests on navigation

**Code Splitting:**
- Lazy load feature pages (auth, cv, analysis, adaptations)

### 8.2 Bundle Size

- Tree-shake unused Tailwind classes
- Use dynamic imports for heavy libraries

---

## 9. Responsive Design

### 9.1 Breakpoints (Tailwind)

- Mobile: < 640px (single column, sidebar collapses)
- Tablet: 640px - 1024px (sidebar in drawer)
- Desktop: > 1024px (sidebar visible)

### 9.2 Mobile Considerations

- Touch-friendly buttons (min 48px)
- Simplified forms (one field per row)
- Readable font sizes (≥16px base)

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Validators (email, URL, file size)
- Zustand store actions (state updates)
- Service layer (API calls mocked)

### 10.2 Integration Tests

- Auth flow (register → login → authenticated)
- CV upload flow
- Analysis creation → result display
- Adaptation generation

### 10.3 E2E Tests (Playwright - optional)

- Full user journey: landing → register → upload CV → analyze → adapt → download

---

## 11. Deployment

### 11.1 Build

```bash
npm run build  # Vite build to dist/
```

### 11.2 Environment Variables

```
VITE_API_URL=https://api.domain.com
VITE_GOOGLE_CLIENT_ID=xxx
```

### 11.3 Hosting

- Vercel (current) or similar
- Auto-deployment on push to main

---

## 12. Key Decisions and Rationale

| Decision | Rationale |
|----------|-----------|
| Zustand (not Redux) | Simpler API, less boilerplate, sufficient for this scale |
| Single store | Consistency, easier debugging, no state fragmentation |
| Feature-based structure | Scalable, clear module boundaries, easy onboarding |
| Axios (not fetch) | Built-in interceptors, request cancellation, better DX |
| React Query | Automatic caching, deduplication, background refetch |
| URL + Text input (not file) | Covers 95% of use cases, simpler UX, backend does scraping |
| HTML preview before PDF | Immediate feedback, user control, backend efficiency |
| JWT + localStorage | Stateless, secure (HTTPS), standard auth pattern |

---

## 13. Success Criteria

✅ User can register/login with email or Google  
✅ User can upload/manage single CV  
✅ User can analyze offer via URL or text  
✅ Analysis results persist in history  
✅ User can generate adapted CV with HTML preview  
✅ User can download PDF of adapted CV  
✅ App is responsive (mobile, tablet, desktop)  
✅ Session persists across page refresh  
✅ Auto-logout on token expiry  
✅ Clear error messages for all failure scenarios  

---

## 14. Next Steps (Implementation)

1. Set up Vite + React + Zustand + React Query project
2. Create API client with interceptors
3. Implement auth feature (register, login, guards)
4. Implement CV management (upload, preview, delete)
5. Implement analysis feature (form, result, history)
6. Implement adaptations feature (preview, download)
7. Style with Tailwind CSS
8. Test critical flows
9. Deploy to Vercel

