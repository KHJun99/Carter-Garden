<template>
  <v-app class="kiosk-app">
    <div class="d-flex flex-column fill-height bg-grey-lighten-5">

      <!-- Title for Registration -->
      <div class="d-flex justify-center pt-6 pb-2">
        <h2 class="text-h4 font-weight-bold" style="color: #166534">사용자 등록</h2>
      </div>

      <div class="d-flex flex-grow-1 align-center justify-center py-4 page-gutter overflow-hidden">

        <v-card
          class="camera-frame rounded-xl elevation-3 d-flex align-center justify-center camera-frame-bg overflow-hidden"
          style="width: 100%; height: 100%; max-height: 75vh;">
          <!-- Live Camera Feed -->
          <img v-if="isConnected" :src="videoUrl" alt="Robot Camera Feed"
            style="width: 100%; height: 100%; object-fit: contain;" />

          <!-- Fallback if not connected -->
          <div v-if="!isConnected" class="position-absolute text-white text-center">
            <v-icon size="64" class="mb-2">mdi-wifi-off</v-icon>
            <div class="text-h5">연결 중...</div>
            <div class="text-subtitle-1 mt-2">IP: {{ JETSON_IP }} (유선)</div>
          </div>
        </v-card>
      </div>

      <footer class="footer-section">
        <div class="footer-container">

          <v-btn class="footer-btn-list" :ripple="false" @click="finishRegistration" :disabled="!isRegisterDone">
            <div class="footer-btn-content">
              <div class="footer-text-list">{{ isRegisterDone ? '등록 완료 및 쇼핑 시작' : '사용자 인식 중...' }}</div>
            </div>
          </v-btn>

        </div>
      </footer>
    </div>
  </v-app>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import rosManager from '@/api/rosManager';
import { JETSON_IP, JETSON_VIDEO_PORT } from '../config';

const router = useRouter();
const isConnected = ref(false);
const isRegisterDone = ref(false);

// ==========================================
// 영상 스트리밍 URL
// ==========================================
const videoUrl = computed(() => {
  return `http://${JETSON_IP}:${JETSON_VIDEO_PORT}/stream?topic=/yolo_result`;
});

// ==========================================
// RosManager 연결 확인 및 상태 구독
// ==========================================
onMounted(() => {
  checkConnection();

  // 로봇으로부터 등록 완료 신호 수신 대기
  rosManager.onStatus((status) => {
    if (status === 'REGISTER_DONE') {
      console.log('Target registration complete signal received.');
      isRegisterDone.value = true;
    }
  });
});

const checkConnection = () => {
  let attempts = 0;
  const interval = setInterval(() => {
    attempts++;
    if (rosManager.isConnected) {
      isConnected.value = true;
      console.log('ROS Manager connected. Sending REGISTER command.');
      rosManager.sendMode('REGISTER');
      clearInterval(interval);
    } else if (attempts > 10) {
      console.warn('ROS Manager not connected after 5 seconds.');
      clearInterval(interval);
    }
  }, 500)
};

const finishRegistration = () => {
  rosManager.sendMode('STOP');
  router.push({ name: 'products' });
};

</script>

<style scoped>
.kiosk-app {
  font-family: var(--kiosk-font);
  user-select: none;
  touch-action: manipulation;
  -webkit-user-drag: none;
  overscroll-behavior: none;
}

.camera-frame {
  border: 4px solid #166534;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.camera-frame-bg {
  background-color: #166534;
}

.footer-section {
  align-items: flex-start;
  background-color: #ffffff;
  border-top: 1px solid #166534;
  display: flex;
  flex-direction: column;
  padding: 2.67vh 1.56vw;
  width: 100%;
  flex-shrink: 0;
  position: relative;
  z-index: 9999;
  transform: translateZ(0);
}

.footer-container {
  align-items: flex-start;
  align-self: stretch;
  display: flex;
  flex: 0 0 auto;
  gap: 1.56vw;
  justify-content: center;
  position: relative;
  width: 100%;
}

.footer-btn-list {
  align-items: center;
  background-color: #166534;
  border-radius: 16px;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  padding: 2.67vh 0px;
  min-height: 10.67vh;
  position: relative;
  width: 90vw;
  cursor: pointer;
  text-transform: none;
  transition: background-color 0.3s ease;
}

.footer-btn-list.v-btn--disabled {
  background-color: #E0E0E0 !important;
  color: #9E9E9E !important;
  box-shadow: none !important;
}

.footer-btn-list.v-btn--disabled .footer-text-list {
  color: #9E9E9E !important;
}

.footer-text-list {
  color: #ffffff;
  font-size: 2.34vw;
  font-weight: 700;
  line-height: 5.33vh;
}
</style>
