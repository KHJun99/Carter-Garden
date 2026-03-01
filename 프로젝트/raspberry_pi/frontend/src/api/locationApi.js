import api from './index';

export const getLocationByCode = async (code) => {
  const response = await api.get('/locations', { params: { location_code: code } });
  return response.data;
};

export const fetchLocationByCategory = async (category) => {
  const response = await api.get('/locations', { params: { category } });
  return response.data;
};

export const getLocationsByCategory = async (category) => {
  const response = await api.get('/locations/', { params: { category } });
  return response.data;
};
