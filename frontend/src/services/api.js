import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

/** Predict type / category / severity without storing */
export const predictComplaint = (text) =>
  api.post('/predict', { text }).then((r) => r.data)

/** Submit complaint → classify + store */
export const submitComplaint = (text) =>
  api.post('/complaint', { text }).then((r) => r.data)

/** List complaints with optional filters + pagination */
export const fetchComplaints = (params = {}) =>
  api.get('/complaints', { params }).then((r) => r.data)

/** Dashboard stats */
export const fetchStats = () =>
  api.get('/stats').then((r) => r.data)

/** Delete a complaint by id */
export const deleteComplaint = (id) =>
  api.delete(`/complaint/${id}`).then((r) => r.data)

export default api
