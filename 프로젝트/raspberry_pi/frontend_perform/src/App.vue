<script setup>
import { onMounted, watch, reactive } from 'vue';
import { storeToRefs } from 'pinia';
import { useCartStore } from '@/store/cart';
import { useUserStore } from '@/store/user';
import { useNavigationStore } from '@/store/navigation';
import { fetchLocationByCategory } from '@/api/locationApi';
import rosManager from '@/api/rosManager';

const cartStore = useCartStore();
const userStore = useUserStore();
const navigationStore = useNavigationStore();
const { lastRfidEvent } = storeToRefs(cartStore);
const snackbar = reactive({ show: false, text: '' });

onMounted(async () => {
  if (userStore.token) {
    await userStore.fetchUserInfo();
  }
  cartStore.loadAllProducts();

  // sessionStorage를 체크하여 새로고침 시에는 다시 쏘지 않도록 함
  const isInitialized = sessionStorage.getItem('robot_initialized');
  if (!isInitialized) {
    try {
      const locations = await fetchLocationByCategory('카트보관함');
      if (Array.isArray(locations) && locations.length > 0) {
        const storage = locations[0];
        // ROS 연결 대기 후 전송 (약간의 딜레이 필요할 수 있음)
        setTimeout(() => {
          rosManager.sendInitialPose(storage.pos_x, storage.pos_y);
          sessionStorage.setItem('robot_initialized', 'true');
          console.log('초기 위치 설정 완료 (최초 1회)');
        }, 1000);
      }
    } catch (error) {
      console.warn('초기 위치 설정 실패:', error);
    }
  } else {
    console.log('이미 초기 위치가 설정되어 있어 전송을 건너뜁니다.');
  };

  // 로봇 위치 실시간 업데이트 구독
  rosManager.onPoseUpdate((data) => {
    navigationStore.updateRobotLocation(data);
  });

  const rfidServerIP = window.location.hostname;
  const socket = new WebSocket(`ws://${rfidServerIP}:8765`);

  socket.onmessage = (event) => {
    const productId = event.data.trim();
    if (productId) {
      console.log('RFID scan received:', productId);
      cartStore.handleRfidScan(productId);
    }
  };
});

watch(() => userStore.token, (nextToken, prevToken) => {
  if (nextToken !== prevToken) {
    cartStore.clearCart();
  }
});

watch(lastRfidEvent, (event) => {
  if (!event || event.action !== 'added') return;
  snackbar.text = '장바구니에 상품이 담겼습니다.';
  snackbar.show = true;
}, { deep: true });
</script>

<template>
  <div class="app-container">
    <v-snackbar v-model="snackbar.show" location="top" :timeout="2500" flat class="kiosk-toast" style="--toast-accent: #4caf50">
      <div class="toast-content">
        <v-icon icon="mdi-check-circle-outline" class="mr-2" size="small" color="success"></v-icon>
        {{ snackbar.text }}
      </div>
    </v-snackbar>
    <router-view />
  </div>
</template>

<style>
:root {
  --kiosk-font: 'Noto Sans KR', 'Nanum Gothic', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
  --kiosk-green-900: #14532d;
  --kiosk-green-800: #166534;
  --kiosk-green-700: #15803d;
  --kiosk-green-600: #16a34a;
  --kiosk-green-100: #dcfce7;
  --kiosk-green-50: #f0fdf4;
  --kiosk-border: #bbf7d0;
  --kiosk-muted: #3f5a4a;
}

html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: var(--kiosk-font);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--kiosk-green-900);
}

body {
  background-color: var(--kiosk-green-50);
  color: var(--kiosk-green-900);
}

.bg-grey-lighten-5 { background-color: var(--kiosk-green-50) !important; }
.bg-grey-lighten-4 { background-color: #ecfdf3 !important; }
.bg-grey-lighten-3 { background-color: #e7f9ee !important; }
.bg-grey-lighten-2 { background-color: #dff5e7 !important; }
.text-grey-darken-1 { color: var(--kiosk-muted) !important; }
.text-grey-darken-2 { color: var(--kiosk-green-800) !important; }

.app-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.page-gutter {
  padding-left: 1.56vw;
  padding-right: 1.56vw;
}

.kiosk-toast .v-snackbar__wrapper {
  background-color: #323232 !important;
  min-width: 45vw !important;
  height: 7vh !important;
  border-radius: 12px !important;
  top: 2vh !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-bottom: 3px solid var(--toast-accent, #ff5252);
}

.kiosk-toast .v-snackbar__content {
  font-size: 2.5vh !important;
  font-family: var(--kiosk-font) !important;
  color: #ffffff !important;
  white-space: nowrap !important;
  display: flex;
  align-items: center;
}
</style>