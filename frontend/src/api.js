// API Gateway — single entry point for all services
const API_BASE = "https://0zm55t7fu0.execute-api.us-east-1.amazonaws.com";

export const PRODUCTS_URL  = `${API_BASE}/v1/products`;
export const CART_URL      = `${API_BASE}/v1/cart`;
export const ORDERS_URL    = `${API_BASE}/v1/orders`;
export const AUTH_URL      = `${API_BASE}/v1/auth`;
export const SEARCH_URL    = `${API_BASE}/v1/search`;

export default API_BASE;
