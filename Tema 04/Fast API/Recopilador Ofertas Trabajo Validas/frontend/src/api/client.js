import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 300_000, // 5 min para generación LaTeX
});

export const fetchOffers = (params = {}) =>
  api.get("/api/offers", { params }).then((r) => r.data);

export const fetchOffer = (id) =>
  api.get(`/api/offers/${id}`).then((r) => r.data);

export const generateCV = (offerId) =>
  api.post(`/api/generate/${offerId}`).then((r) => r.data);

export const uploadMasterCV = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/upload-master-cv", form).then((r) => r.data);
};

export default api;
