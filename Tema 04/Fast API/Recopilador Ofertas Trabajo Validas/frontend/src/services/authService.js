import apiClient from './apiClient';

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
