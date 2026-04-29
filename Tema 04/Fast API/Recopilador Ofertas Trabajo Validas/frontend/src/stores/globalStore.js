import { create } from 'zustand';
import { authService } from '../services/authService';
import { cvService } from '../services/cvService';
import { analysisService } from '../services/analysisService';
import { adaptationService } from '../services/adaptationService';
import { profileService } from '../services/profileService';

const useStore = create((set, get) => ({
  // ===== AUTH SLICE =====
  auth: {
    user: null,
    token: null,
    isLoading: false,
    error: null,
  },

  authActions: {
    setUser: (user) => set((state) => ({ auth: { ...state.auth, user } })),
    setToken: (token) => {
      set((state) => ({ auth: { ...state.auth, token } }));
      if (token) localStorage.setItem('token', token);
      else localStorage.removeItem('token');
    },

    login: async (email, password) => {
      set((state) => ({ auth: { ...state.auth, isLoading: true, error: null } }));
      try {
        const response = await authService.login(email, password);
        console.log('Login response:', response);
        const { access_token, user_id, email: userEmail } = response.data;

        if (!access_token || !user_id) {
          throw new Error('Invalid response structure: missing access_token or user_id');
        }

        const token = access_token;
        const user = { id: user_id, email: userEmail };

        set((state) => ({
          auth: { ...state.auth, user, token, isLoading: false, error: null },
        }));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        console.log('Login successful, token stored');
        get().profileActions.loadProfile();
        return { success: true };
      } catch (error) {
        console.error('Login error:', error);
        const message = error.response?.data?.detail || error.message || 'Login failed';
        set((state) => ({ auth: { ...state.auth, isLoading: false, error: message } }));
        return { success: false, error: message };
      }
    },

    registerUser: async (email, password, name) => {
      set((state) => ({ auth: { ...state.auth, isLoading: true, error: null } }));
      try {
        const response = await authService.register(email, password, name);
        const { access_token, user_id, email: userEmail } = response.data;

        const token = access_token;
        const user = { id: user_id, email: userEmail };

        set((state) => ({
          auth: { ...state.auth, user, token, isLoading: false, error: null },
        }));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        get().profileActions.loadProfile();
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'Registration failed';
        set((state) => ({ auth: { ...state.auth, isLoading: false, error: message } }));
        return { success: false, error: message };
      }
    },

    googleCallback: async (code) => {
      set((state) => ({ auth: { ...state.auth, isLoading: true, error: null } }));
      try {
        const response = await authService.googleCallback(code);
        const { access_token, user_id, email: userEmail } = response.data;

        const token = access_token;
        const user = { id: user_id, email: userEmail };

        set((state) => ({
          auth: { ...state.auth, user, token, isLoading: false, error: null },
        }));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        get().profileActions.loadProfile();
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'Google auth failed';
        set((state) => ({ auth: { ...state.auth, isLoading: false, error: message } }));
        return { success: false, error: message };
      }
    },

    logout: () => {
      set({
        auth: { user: null, token: null, isLoading: false, error: null },
        cv: { currentCV: null, isUploading: false, error: null },
      });
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },

    restoreSession: async () => {
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr);
          set((state) => ({ auth: { ...state.auth, user, token } }));
          const response = await authService.getMe();
          set((state) => ({ auth: { ...state.auth, user: response.data } }));
          get().profileActions.loadProfile();
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
    },
  },

  // ===== PROFILE SLICE =====
  profile: {
    data: null,
    isLoading: false,
    error: null,
  },

  profileActions: {
    loadProfile: async () => {
      set((state) => ({ profile: { ...state.profile, isLoading: true, error: null } }));
      try {
        const response = await profileService.getProfile();
        set((state) => ({ profile: { ...state.profile, data: response, isLoading: false, error: null } }));
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'Failed to load profile';
        set((state) => ({ profile: { ...state.profile, isLoading: false, error: message } }));
        return { success: false, error: message };
      }
    },
  },

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

  // ===== CV SLICE =====
  cv: {
    currentCV: null,
    isLoading: false,
    isUploading: false,
    error: null,
  },

  cvActions: {
    setCurrentCV: (cv) => set((state) => ({ cv: { ...state.cv, currentCV: cv } })),

    uploadCV: async (file) => {
      set((state) => ({ cv: { ...state.cv, isUploading: true, error: null } }));
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await cvService.uploadCV(formData);
        set((state) => ({
          cv: { ...state.cv, currentCV: response.data, isUploading: false, error: null },
        }));
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'CV upload failed';
        set((state) => ({ cv: { ...state.cv, isUploading: false, error: message } }));
        return { success: false, error: message };
      }
    },

    deleteCV: async () => {
      try {
        await cvService.deleteCV();
        set((state) => ({ cv: { ...state.cv, currentCV: null } }));
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'CV deletion failed';
        set((state) => ({ cv: { ...state.cv, error: message } }));
        return { success: false, error: message };
      }
    },

    fetchCurrentCV: async () => {
      set((state) => ({ cv: { ...state.cv, isLoading: true, error: null } }));
      try {
        const response = await cvService.getCV();
        set((state) => ({ cv: { ...state.cv, currentCV: response.data, isLoading: false } }));
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'Failed to load CV';
        set((state) => ({ cv: { ...state.cv, isLoading: false, error: message } }));
        return { success: false };
      }
    },
  },

  // ===== ANALYSIS SLICE =====
  analysis: {
    analyses: [],
    currentAnalysis: null,
    isAnalyzing: false,
    isLoadingHistory: false,
    totalAnalyses: 0,
    error: null,
  },

  analysisActions: {
    setCurrentAnalysis: (analysis) =>
      set((state) => ({ analysis: { ...state.analysis, currentAnalysis: analysis } })),

    addAnalysisToHistory: (analysis) =>
      set((state) => ({
        analysis: {
          ...state.analysis,
          analyses: [analysis, ...state.analysis.analyses],
        },
      })),

    createAnalysis: async (input) => {
      set((state) => ({ analysis: { ...state.analysis, isAnalyzing: true, error: null } }));
      try {
        const response = await analysisService.createAnalysis(input);
        set((state) => ({
          analysis: {
            ...state.analysis,
            currentAnalysis: response.data,
            isAnalyzing: false,
            error: null,
          },
        }));
        get().analysisActions.addAnalysisToHistory(response.data);
        return { success: true, data: response.data };
      } catch (error) {
        const message = error.response?.data?.detail || 'Analysis creation failed';
        set((state) => ({
          analysis: { ...state.analysis, isAnalyzing: false, error: message },
        }));
        return { success: false, error: message };
      }
    },

    loadAnalysisHistory: async (limit = 10, offset = 0) => {
      set((state) => ({ analysis: { ...state.analysis, isLoadingHistory: true } }));
      try {
        const response = await analysisService.getAnalysisHistory(limit, offset);
        set((state) => ({
          analysis: {
            ...state.analysis,
            analyses: response.data.items || [],
            totalAnalyses: response.data.total || 0,
            isLoadingHistory: false,
          },
        }));
        return { success: true, total: response.data.total || 0, itemsCount: (response.data.items || []).length };
      } catch (error) {
        console.error('Error loading analysis history:', error);
        set((state) => ({ analysis: { ...state.analysis, isLoadingHistory: false } }));
        return { success: false };
      }
    },
  },

  // ===== ADAPTATIONS SLICE =====
  adaptations: {
    adaptations: [],
    currentAdaptation: null,
    isGenerating: false,
    isLoadingHistory: false,
    total: 0,
    error: null,
  },

  adaptationActions: {
    setCurrentAdaptation: (adaptation) =>
      set((state) => ({ adaptations: { ...state.adaptations, currentAdaptation: adaptation } })),

    createAdaptation: async (analysisId) => {
      set((state) => ({
        adaptations: { ...state.adaptations, isGenerating: true, error: null },
      }));
      try {
        const response = await adaptationService.createAdaptation(analysisId);
        set((state) => ({
          adaptations: {
            ...state.adaptations,
            currentAdaptation: response.data,
            isGenerating: false,
            error: null,
          },
        }));
        return { success: true, data: response.data };
      } catch (error) {
        const message = error.response?.data?.detail || 'Adaptation generation failed';
        set((state) => ({
          adaptations: { ...state.adaptations, isGenerating: false, error: message },
        }));
        return { success: false, error: message };
      }
    },

    loadAdaptationHistory: async (limit = 10, offset = 0) => {
      set((state) => ({
        adaptations: { ...state.adaptations, isLoadingHistory: true },
      }));
      try {
        const response = await adaptationService.getAdaptationHistory(limit, offset);
        set((state) => ({
          adaptations: {
            ...state.adaptations,
            adaptations: response.data.items || response.data || [],
            total: response.data.total || 0,
            isLoadingHistory: false,
          },
        }));
        return { success: true, total: response.data.total || 0, itemsCount: (response.data.items || response.data || []).length };
      } catch (error) {
        console.error('Error loading adaptation history:', error);
        set((state) => ({
          adaptations: { ...state.adaptations, isLoadingHistory: false },
        }));
        return { success: false };
      }
    },

    loadAdaptation: async (id) => {
      try {
        const response = await adaptationService.getAdaptation(id);
        set((state) => ({
          adaptations: { ...state.adaptations, currentAdaptation: response.data },
        }));
        return { success: true, data: response.data };
      } catch (error) {
        return { success: false, error: 'Adaptation not found' };
      }
    },

    downloadPDF: async (adaptationId) => {
      try {
        const state = get();
        const adaptation = state.adaptations.currentAdaptation;
        const profile = state.profile.data;

        let filename = `cv_adaptation_${adaptationId}.pdf`;

        if (adaptation && profile?.cv_data?.nombre) {
          const normalizeFilename = (text) => {
            if (!text) return '';
            const nfkd = text.normalize('NFKD');
            let normalized = '';
            for (let i = 0; i < nfkd.length; i++) {
              const code = nfkd.charCodeAt(i);
              if (code < 0x0300 || code > 0x036F) {
                normalized += nfkd[i];
              }
            }
            normalized = normalized.replace(/[^a-zA-Z0-9]+/g, '_');
            normalized = normalized.replace(/^_+|_+$/g, '');
            return normalized;
          };

          const jobTitle = normalizeFilename(adaptation.job_title || 'Oferta');
          const company = normalizeFilename(adaptation.company || 'Empresa');
          const candidateName = normalizeFilename(profile.cv_data.nombre);

          filename = `${jobTitle}_${company}_${candidateName}.pdf`;
        }

        const response = await adaptationService.downloadPDF(adaptationId);
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        return { success: true };
      } catch (error) {
        return { success: false, error: 'PDF download failed' };
      }
    },
  },
}));

export default useStore;
