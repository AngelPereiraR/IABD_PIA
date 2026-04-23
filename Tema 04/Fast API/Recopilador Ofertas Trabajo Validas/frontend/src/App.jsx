import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import useStore from './stores/globalStore';

// Pages & Components
import { LandingPage } from './features/landing/pages/LandingPage';
import { LoginPage } from './features/auth/pages/LoginPage';
import { RegisterPage } from './features/auth/pages/RegisterPage';
import { GoogleCallbackPage } from './features/auth/pages/GoogleCallbackPage';
import { DashboardPage } from './features/dashboard/pages/DashboardPage';
import { CVPage } from './features/cv/pages/CVPage';
import { AnalysisPage } from './features/analysis/pages/AnalysisPage';
import { ResultPage } from './features/analysis/pages/ResultPage';
import { HistoryPage } from './features/analysis/pages/HistoryPage';
import { AdaptationPage } from './features/adaptations/pages/AdaptationPage';
import ProfilePage from './features/profile/pages/ProfilePage';
import { ProtectedRoute, CVRequiredRoute } from './shared/components';

const qc = new QueryClient();

function App() {
  const { token, restoreSession } = useStore((state) => ({
    token: state.auth.token,
    restoreSession: state.authActions.restoreSession,
  }));

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />

          {/* Auth Routes */}
          <Route path="/auth/login" element={token ? <Navigate to="/dashboard" /> : <LoginPage />} />
          <Route path="/auth/register" element={token ? <Navigate to="/dashboard" /> : <RegisterPage />} />
          <Route path="/auth/google-callback" element={<GoogleCallbackPage />} />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/cv"
            element={
              <ProtectedRoute>
                <CVPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/analysis"
            element={
              <ProtectedRoute>
                <CVRequiredRoute>
                  <AnalysisPage />
                </CVRequiredRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/analysis/:id"
            element={
              <ProtectedRoute>
                <CVRequiredRoute>
                  <ResultPage />
                </CVRequiredRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/analysis/history"
            element={
              <ProtectedRoute>
                <CVRequiredRoute>
                  <HistoryPage />
                </CVRequiredRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/adaptations/:analysisId"
            element={
              <ProtectedRoute>
                <CVRequiredRoute>
                  <AdaptationPage />
                </CVRequiredRoute>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
