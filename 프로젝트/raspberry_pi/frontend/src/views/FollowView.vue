<template>
  <v-app class="kiosk-app">
    <div class="d-flex flex-column fill-height bg-grey-lighten-5">

      <div class="d-flex flex-grow-1 align-center justify-center py-6 page-gutter overflow-hidden">

        <v-card
          class="camera-frame rounded-xl elevation-3 d-flex align-center justify-center camera-frame-bg overflow-hidden"
          style="width: 100%; height: 100%; max-height: 80vh;">
          <img v-if="isConnected" :src="videoUrl" alt="Robot Camera Feed"
            style="width: 100%; height: 100%; object-fit: contain;" />

          <div v-if="!isConnected" class="position-absolute text-white text-center">
            <v-icon size="64" class="mb-2">mdi-wifi-off</v-icon>
            <div class="text-h5">연결 중...</div>
            <div class="text-subtitle-1 mt-2">IP: {{ JETSON_IP }} (유선)</div>
          </div>
        </v-card>
      </div>

      <footer class="footer-section">
        <div class="footer-container">

          <v-btn class="footer-btn-follow" variant="outlined" :ripple="false" @click="goToProductList">
            <div class="footer-btn-content">
              <div class="footer-icon-wrapper">
                <v-img :src="iconToList" alt="List" class="footer-icon-follow"></v-img>
              </div>
              <div class="footer-text-follow">상품 목록</div>
            </div>
          </v-btn>

          <v-btn class="footer-btn-list" :ripple="false" @pointerup.stop="togglePause">
            <div class="footer-btn-content">
              <v-img :src="btnIconSrc" alt="pause/play icon" class="footer-icon-list"></v-img>
              <div class="footer-text-list">{{ pauseLabel }}</div>
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

// Icon Imports
import iconToList from '@/assets/ToListGreen.png';
import pauseIcon from '@/assets/Stop.png';
import playIcon from '@/assets/play.png';
import { JETSON_IP, JETSON_VIDEO_PORT } from '../config';

const router = useRouter();
const isConnected = ref(false);
const isPaused = ref(false);

// ==========================================
// 영상 스트리밍 URL
// ==========================================
const videoUrl = computed(() => {
  return `http://${JETSON_IP}:${JETSON_VIDEO_PORT}/stream?topic=/yolo_result`;
});

// ==========================================
// RosManager 연결
// ==========================================
onMounted(() => {
  checkConnection();
});

const checkConnection = () => {
  let attempts = 0;
  const interval = setInterval(() => {
    attempts++;
    if (rosManager.isConnected) {
      isConnected.value = true;
      console.log('ROS Manager connected. Sending FOLLOW command.');
      rosManager.sendMode('FOLLOW');
      clearInterval(interval);
    } else if (attempts > 10) {
      console.warn('ROS Manager not connected after 5 seconds.');
      clearInterval(interval);
    }
  }, 500)
};

// ==========================================
// 4. 버튼 이벤트 핸들러
// ==========================================
const togglePause = () => {
  isPaused.value = !isPaused.value;
  const command = isPaused.value ? 'STOP' : 'FOLLOW';
  rosManager.sendMode(command);
};

const pauseLabel = computed(() => (isPaused.value ? '주행 시작' : '일시 정지'));
const btnIconSrc = computed(() => (isPaused.value ? playIcon : pauseIcon));

const goToProductList = () => {
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

.footer-btn-follow {
  align-items: center;
  border: 1px solid #166534;
  border-radius: 16px;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  padding: 2.67vh 0px;
  min-height: 10.67vh;
  position: relative;
  width: 47.75vw;
  cursor: pointer;
  text-transform: none;
}

.footer-btn-content {
  display: flex;
  align-items: center;
  gap: 0.78vw;
}

.footer-icon-wrapper {
  align-items: flex-start;
  display: inline-flex;
  flex: 0 0 auto;
  flex-direction: column;
  position: relative;
}

.footer-icon-follow {
  height: 4vh;
  width: 2.34vw;
  color: #14532d;
}

.footer-text-follow {
  color: #14532d;
  font-size: 2.34vw;
  font-weight: 700;
  line-height: 5.33vh;
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
  width: 47.56vw;
  cursor: pointer;
  text-transform: none;
}

.footer-icon-list {
  height: 4vh;
  width: 2.34vw;
  filter: brightness(0) invert(1);
}

.footer-text-list {
  color: #ffffff;
  font-size: 2.34vw;
  font-weight: 700;
  line-height: 5.33vh;
}
</style>
