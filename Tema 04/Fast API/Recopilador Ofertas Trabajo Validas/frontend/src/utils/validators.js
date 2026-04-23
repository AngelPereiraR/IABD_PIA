export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const isValidURL = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isValidPDF = (file) => {
  if (!file) return false;
  return file.type === 'application/pdf' && file.size < 10 * 1024 * 1024; // 10MB
};

export const isValidTextLength = (text, min = 50, max = 5000) => {
  const length = text.trim().length;
  return length >= min && length <= max;
};
