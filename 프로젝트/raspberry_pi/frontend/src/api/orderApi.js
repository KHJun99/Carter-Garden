import api from './index';

export const searchParkingByCarNumber = async (carNumber) => {
  const response = await api.get('/parking/search', { params: { car_number: carNumber } });
  return response.data;
};
