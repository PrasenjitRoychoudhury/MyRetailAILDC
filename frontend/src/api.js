import axios from 'axios';

const API_BASE = "https://0zm55t7fu0.execute-api.us-east-1.amazonaws.com";

const api = {
  // Products
  getProducts: (params = {}) =>
    axios.get(`${API_BASE}/v1/products`, { params }),

  getProduct: (id) =>
    axios.get(`${API_BASE}/v1/products/${id}`),

  getCategories: () =>
    axios.get(`${API_BASE}/v1/products/categories`),

  // Search
  search: (params = {}) =>
    axios.get(`${API_BASE}/v1/search`, { params }),

  // Cart
  getCart: (sessionId) =>
    axios.get(`${API_BASE}/v1/cart/${sessionId}`),

  addToCart: (sessionId, item) =>
    axios.post(`${API_BASE}/v1/cart/${sessionId}/items`, item),

  updateCart: (sessionId, productId, data) =>
    axios.put(`${API_BASE}/v1/cart/${sessionId}/items/${productId}`, data),

  removeFromCart: (sessionId, productId) =>
    axios.delete(`${API_BASE}/v1/cart/${sessionId}/items/${productId}`),

  checkout: (sessionId, data) =>
    axios.post(`${API_BASE}/v1/cart/${sessionId}/checkout`, data),

  // Orders
  getOrder: (orderId) =>
    axios.get(`${API_BASE}/v1/orders/${orderId}`),

  // Auth
  register: (data) =>
    axios.post(`${API_BASE}/v1/auth/register`, data),

  login: (data) =>
    axios.post(`${API_BASE}/v1/auth/login`, data),

  validate: (token) =>
    axios.post(`${API_BASE}/v1/auth/validate`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    }),
  getSimilarProducts: (productId) =>
    axios.get(`${API_BASE}/v1/similar/${productId}`),
};

export default api;
