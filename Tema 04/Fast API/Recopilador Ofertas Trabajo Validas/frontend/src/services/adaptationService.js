import apiClient from './apiClient';

export const adaptationService = {
  createAdaptation: (analysisId) =>
    apiClient.post('/adaptations/create', { analysis_id: analysisId }),

  getAdaptationHistory: (limit = 10, offset = 0) =>
    apiClient.get('/adaptations/history', {
      params: { limit, offset },
    }),

  getAdaptation: (id) =>
    apiClient.get(`/adaptations/${id}`),

  downloadPDF: (id) =>
    apiClient.get(`/adaptations/${id}/download-pdf`, {
      responseType: 'arraybuffer',
    }),
};
