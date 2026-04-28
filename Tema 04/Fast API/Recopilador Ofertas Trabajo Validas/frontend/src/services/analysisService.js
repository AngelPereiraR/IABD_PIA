import apiClient from './apiClient';

export const analysisService = {
  createAnalysis: (input) =>
    apiClient.post('/analysis/create', input),

  getAnalysisHistory: (limit = 10, offset = 0) =>
    apiClient.get('/analysis/list', {
      params: { limit, offset },
    }),

  getAnalysis: (id) =>
    apiClient.get(`/analysis/${id}`),
};
