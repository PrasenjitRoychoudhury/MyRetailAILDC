import axios from 'axios'
const PRODUCTS = 'https://k7gmrg2weg.us-east-1.awsapprunner.com'
const CART     = 'https://kct6edawdr.us-east-1.awsapprunner.com'
const ORDERS   = 'https://7xkmpkbemc.us-east-1.awsapprunner.com'
const SEARCH   = 'https://wdtp3dmewx.us-east-1.awsapprunner.com'
export const api = {
  getProducts:   (params)     => axios.get(`${PRODUCTS}/v1/products`, { params }),
  getProduct:    (id)         => axios.get(`${PRODUCTS}/v1/products/${id}`),
  getCategories: ()           => axios.get(`${PRODUCTS}/v1/categories`),
  search:        (params)     => axios.get(`${SEARCH}/v1/search`, { params }),
  getCart:       (sid)        => axios.get(`${CART}/v1/cart/${sid}`),
  addToCart:     (sid, d)     => axios.post(`${CART}/v1/cart/${sid}/items`, d),
  updateCart:    (sid, pid, d)=> axios.put(`${CART}/v1/cart/${sid}/items/${pid}`, d),
  removeFromCart:(sid, pid)   => axios.delete(`${CART}/v1/cart/${sid}/items/${pid}`),
  checkout:      (sid, d)     => axios.post(`${CART}/v1/cart/${sid}/checkout`, d),
}
export default api
