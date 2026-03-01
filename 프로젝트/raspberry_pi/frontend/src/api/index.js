import axios from 'axios'
import { useUserStore } from '@/store/user';
import { API_URL } from '@/config';

const api = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 2. [요청 인터셉터] 전송 전 토큰 실어 보내기
api.interceptors.request.use(
  (config) => {

    // 인터셉터 내부에서 store 호출
    const userStore = useUserStore();

    // 스토어에 있는 token 바로 가져다 씀.
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 3. [응답 인터셉터] 토큰 만료(401) 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const userStore = useUserStore();

      // 401 에러(인증 실패)가 나면 로그아웃 처리 후 로그인 페이지로
      userStore.logout();

      //
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api
