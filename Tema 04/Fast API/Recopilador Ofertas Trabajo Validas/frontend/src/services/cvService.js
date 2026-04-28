import apiClient from './apiClient';

export const cvService = {
  uploadCV: (formData) =>
    apiClient.post('/cv/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getCV: () =>
    apiClient.get('/cv/current'),

  deleteCV: () =>
    apiClient.delete('/cv/current'),
};
