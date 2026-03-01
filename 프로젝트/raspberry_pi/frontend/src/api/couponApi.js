import api from './index';

export const getUserCoupons = async (userId) => {
  const response = await api.get(`/coupons/${userId}`);
  return response.data;
};

export const useCoupon = async (couponId) => {
  const response = await api.post(`/coupons/use/${couponId}`);
  return response.data;
};
