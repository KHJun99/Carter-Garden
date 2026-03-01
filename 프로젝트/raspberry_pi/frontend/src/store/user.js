// src/store/user.js
import { defineStore } from 'pinia';
import axios from '@/api/index'; // 위에서 만든 axios 인스턴스 import

export const useUserStore = defineStore('user', {
  // 1. 상태(State): 변수들
  state: () => ({
    token: localStorage.getItem('accessToken') || null, // 새로고침해도 유지
    userInfo: null, // 사용자 정보 (이름, ID 등)
  }),

  // 2. 게터(Getters): 계산된 값
  getters: {
    isAuthenticated: (state) => !!state.token, // 토큰이 있으면 로그인 상태 true
    getUserName: (state) => state.userInfo?.user_name || '비회원',
  },

  // 3. 액션(Actions): 함수들
  actions: {
    // 로그인 함수
    async login(loginId, password) {
      try {
        // 백엔드 로그인 API 호출
        const response = await axios.post('/users/login', {
          login_id: loginId,
          password: password,
        });

        // 응답에서 토큰 추출 (백엔드 응답 구조: { data: { access_token: ... } })
        const { access_token, user_name, user_id } = response.data.data;

        // 상태 및 로컬스토리지 저장
        this.token = access_token;
        localStorage.setItem('accessToken', access_token);

        // 사용자 기본 정보도 일단 저장 (필요시 /me 호출로 갱신)
        this.userInfo = { user_name, user_id };

        return true; // 성공
      } catch (error) {
        console.error('로그인 실패:', error);
        throw error; // 컴포넌트에서 에러 처리하도록 던짐
      }
    },

    // 내 정보 상세 조회 함수 (/me)
    async fetchUserInfo() {
      if (!this.token) return;
      try {
        const response = await axios.get('/users/me');
        this.userInfo = response.data.data;
      } catch (error) {
        console.error('내 정보 조회 실패:', error);
        this.logout(); // 정보 조회 실패 시(토큰 변조 등) 로그아웃
      }
    },

    // 로그아웃
    logout() {
      //Pinia 초기화
      this.token = null;
      this.userInfo = null;
      //브라우저 저장소 삭제
      localStorage.removeItem('accessToken');
    },
  },
});