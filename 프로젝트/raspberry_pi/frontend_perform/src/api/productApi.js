import api from './index';

export const getProducts = async (params = {}) => {
  const response = await api.get('/products/', { params });
  return response.data;
};

export const getCategories = async () => {
  const response = await api.get('/products/categories');
  return response.data;
};

export const getProductDetail = async (productId) => {
  const response = await api.get(`/products/${productId}`);
  return response.data;
};

export const getRecommendation = async (productIds) => {
  const response = await api.post('/products/recommend', { product_ids: productIds });
  return response.data;
};

export const getAiRecommendation = async (currentCartIds) => {
  const response = await api.post('/products/recommend', { 
    product_ids: currentCartIds 
  });
  return response.data;
};