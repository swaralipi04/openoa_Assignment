import axios from 'axios';

// In dev, Vite proxy handles /api/* → http://localhost:8000/api/*
// In production, we point directly to the Cloud Run backend
const API_BASE = import.meta.env.VITE_API_URL || 'https://openoa-backend-997295316879.asia-south1.run.app';

const api = axios.create({
    baseURL: `${API_BASE}/api`,
    timeout: 120000, // 2 min — analyses can be slow
    headers: { 'Content-Type': 'application/json' },
});

/* ── Health ── */
export const getHealth = () => api.get('/health');

/* ── Data ── */
export const loadExampleData = () => api.post('/data/example');

export const uploadData = (formData) =>
    api.post('/data/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
    });

export const listDatasets = () => api.get('/data/datasets');

export const deleteDataset = (datasetId) =>
    api.delete(`/data/${datasetId}`);

/* ── Analysis ── */
export const runAnalysis = (endpoint, params) =>
    api.post(`/analysis/${endpoint}`, params);

export default api;
