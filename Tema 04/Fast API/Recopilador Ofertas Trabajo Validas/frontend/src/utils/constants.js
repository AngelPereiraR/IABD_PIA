export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:7860';

export const FILE_SIZE_LIMITS = {
  PDF_MAX: 10 * 1024 * 1024, // 10MB
};

export const TEXT_VALIDATION = {
  ANALYSIS_MIN: 50,
  ANALYSIS_MAX: 5000,
};

export const PAGINATION = {
  DEFAULT_LIMIT: 10,
  DEFAULT_OFFSET: 0,
};

export const TOAST_DURATION = {
  SHORT: 2000,
  MEDIUM: 3000,
  LONG: 5000,
};

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
};

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Your session has expired. Please login again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  INVALID_FILE: 'Invalid file type or size. PDF files up to 10MB are supported.',
  INVALID_URL: 'Please provide a valid URL.',
  INVALID_TEXT: 'Please provide text between 50 and 5000 characters.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
};
