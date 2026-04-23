import { create } from 'zustand';
import { authService } from '../services/authService';
import { cvService } from '../services/cvService';
import { analysisService } from '../services/analysisService';
import { adaptationService } from '../services/adaptationService';

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
        const { token, user } = response.data;
        set((state) => ({
          auth: { ...state.auth, user, token, isLoading: false, error: null },
        }));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        return { success: true };
      } catch (error) {
        const message = error.response?.data?.detail || 'Login failed';
        set((state) => ({ auth: { ...state.auth, isLoading: false, error: message } }));
        return { success: false, error: message };
      }
    },

    registerUser: async (email, password, name) => {
      set((state) => ({ auth: { ...state.auth, isLoading: true, error: null } }));
      try {
        const response = await authService.register(email, password, name);
        const { token, user } = response.data;
        set((state) => ({
          auth: { ...state.auth, user, token, isLoading: false, error: null },
        }));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
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
        const { token, user } = response.data;
        set((state) => ({
          auth: { ...state.auth, user, token, isLoading: false, error: null },
        }));
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
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
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
    },
  },

  // ===== CV SLICE =====
  cv: {
    currentCV: null,
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
      try {
        const response = await cvService.getCV();
        set((state) => ({ cv: { ...state.cv, currentCV: response.data } }));
        return { success: true };
      } catch (error) {
        return { success: false };
      }
    },
  },

  // ===== ANALYSIS SLICE =====
  analysis: {
    analyses: [],
    currentAnalysis: null,
    isAnalyzing: false,
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
      try {
        const response = await analysisService.getAnalysisHistory(limit, offset);
        set((state) => ({
          analysis: { ...state.analysis, analyses: response.data },
        }));
        return { success: true };
      } catch (error) {
        return { success: false };
      }
    },
  },

  // ===== ADAPTATIONS SLICE =====
  adaptations: {
    adaptations: [],
    currentAdaptation: null,
    isGenerating: false,
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
      try {
        const response = await adaptationService.getAdaptationHistory(limit, offset);
        set((state) => ({
          adaptations: { ...state.adaptations, adaptations: response.data },
        }));
        return { success: true };
      } catch (error) {
        return { success: false };
      }
    },

    downloadPDF: async (adaptationId) => {
      try {
        const response = await adaptationService.downloadPDF(adaptationId);
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cv_adaptation_${adaptationId}.pdf`;
        a.click();
        return { success: true };
      } catch (error) {
        return { success: false, error: 'PDF download failed' };
      }
    },
  },
}));

export default useStore;
