<template>
  <main class="finish-page">
    <header class="hero">
      <h1>쇼핑이 끝났습니다!</h1>
      <p>카트를 어떻게 도와드릴까요?</p>
    </header>

    <section class="choice-grid">
      <button class="choice-card return" type="button" @click="goThanks">
        <div class="icon-circle">
          <v-icon size="10vh" color="white">mdi-tray-arrow-down</v-icon>
        </div>
        <span class="choice-title">여기서 바로 반납</span>
        <span class="choice-desc">카트 반납함으로 자율주행합니다.</span>
      </button>

      <button class="choice-card park" type="button" @click="openParkingModal">
        <div class="icon-circle">
          <v-icon size="10vh" color="white">mdi-car-select</v-icon>
        </div>
        <span class="choice-title">주차장까지 이동</span>
        <span class="choice-desc">차량 앞까지 카트가 따라옵니다.</span>
      </button>
    </section>

    <div v-if="showParkingModal" class="modal-overlay" @click.self="closeParkingModal">
      <div :class="['parking-modal', { 'keyboard-up': showParkingKeyboard }]">
        <div class="modal-header">
          <h2>주차 위치 입력</h2>
          <v-btn icon="mdi-close" variant="text" @click="closeParkingModal"></v-btn>
        </div>

        <div class="modal-body">
          <div class="field">
            <input ref="parkingInput" v-model="parkingSpot" type="text" placeholder="차량 번호 뒷 4자리 입력"
              @focus="showParkingKeyboard = true" />

            <!-- 검색 결과 리스트 -->
            <div v-if="searchResults.length > 0" class="search-results">
              <div v-for="car in searchResults" :key="car.park_info_id" class="search-item" @click="selectCar(car)">
                <span class="car-num">{{ car.car_number }}</span>
                <span class="loc-code">{{ car.location ? car.location.location_code : '위치 정보 없음' }}</span>
              </div>
            </div>
          </div>
          <button class="primary-btn" type="button" @click="goGuide">
            이동 시작
          </button>
        </div>
      </div>
    </div>

    <virtual-keyboard :isActive="showParkingKeyboard" @input="handleParkingKeyboardInput"
      @done="showParkingKeyboard = false" @close="showParkingKeyboard = false" />

    <v-snackbar v-model="snackbar.show" location="top" :timeout="3000" flat class="kiosk-toast">
      <div class="toast-content">
        <v-icon icon="mdi-alert-circle-outline" class="mr-2" size="small"></v-icon>
        {{ snackbar.text }}
      </div>
    </v-snackbar>
  </main>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useNavigationStore } from '@/store/navigation'
import VirtualKeyboard from '@/components/common/VirtualKeyboard.vue'
import { getLocationByCode } from '@/api/locationApi' // [수정] 코드 기반 조회로 변경
import { searchParkingByCarNumber } from '@/api/orderApi'
import rosManager from '@/api/rosManager'
import { applyVirtualKeyboardInput } from '@/utils/keyboardInput'

const router = useRouter()
const userStore = useUserStore()
const navStore = useNavigationStore()

const showParkingModal = ref(false)
const parkingSpot = ref('')
const showParkingKeyboard = ref(false)

const searchResults = ref([])
const selectedLocation = ref(null)
const snackbar = reactive({ show: false, text: '' })

const openParkingModal = () => {
  showParkingModal.value = true
  parkingSpot.value = ''
  searchResults.value = []
  selectedLocation.value = null
}

const closeParkingModal = () => {
  showParkingModal.value = false
  showParkingKeyboard.value = false
}

const handleParkingKeyboardInput = (key) => {
  if (key === 'Enter') {
    showParkingKeyboard.value = false
    performSearch()
  } else {
    parkingSpot.value = applyVirtualKeyboardInput(parkingSpot.value, key)
  }
}

watch(parkingSpot, (newVal) => {
  if (newVal.length >= 4) {
    performSearch()
  } else {
    searchResults.value = []
  }
})

const performSearch = async () => {
  if (parkingSpot.value.length < 2) return;
  try {
    const data = await searchParkingByCarNumber(parkingSpot.value);
    searchResults.value = data || [];
  } catch (error) {
    console.error(error);
  }
}

const selectCar = (car) => {
  parkingSpot.value = car.car_number;
  selectedLocation.value = car.location;
  searchResults.value = [];
  showParkingKeyboard.value = false;
}

const goThanks = async () => {
  try {
    if (!navStore.mapLoaded) await navStore.initMap();

    // 카트보관함(STOR-001) 명시적 조회
    const storageLocation = await getLocationByCode('STOR-001');

    if (storageLocation) {
      const payload = navStore.getNavigationPayload(navStore.currentLocationCode, storageLocation.location_code);
      if (payload) {
        rosManager.sendDestination(payload);
      } else {
        console.error("반납 경로 생성 실패");
      }
    } else {
      console.warn('카트보관함 위치 정보를 찾을 수 없습니다.');
    }
  } catch (error) {
    console.error(error);
  }

  userStore.logout();
  router.push('/thanks');
}

const goGuide = async () => {
  if (!selectedLocation.value) {
    snackbar.text = '차량을 검색하여 선택해주세요.';
    snackbar.show = true;
    return;
  }

  if (!navStore.mapLoaded) await navStore.initMap();

  // [수정] 주차장 경로 생성 및 전송
  const targetCode = selectedLocation.value.location_code;
  const payload = navStore.getNavigationPayload(navStore.currentLocationCode, targetCode);

  if (payload) {
    rosManager.sendDestination(payload);
  } else {
    console.error("주차장 경로 생성 실패");
  }

  router.push({
    name: 'guide',
    query: {
      from: 'finish',
      name: `내 차 (${parkingSpot.value})`,
      code: targetCode,
      x: selectedLocation.value.pos_x,
      y: selectedLocation.value.pos_y
    }
  });
}
</script>

<style scoped>
.finish-page {
  width: 100vw;
  height: 100vh;
  padding: 4vh 5vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f5f5f5;
  font-family: var(--kiosk-font);
  overflow: hidden;
}

.hero {
  text-align: center;
  margin-bottom: 4vh;
}

.hero h1 {
  font-size: 6vh;
  margin: 0;
  color: #14532d;
}

.hero p {
  font-size: 3vh;
  color: #666;
  margin-top: 1vh;
}

.choice-grid {
  flex: 1;
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3vw;
}

.choice-card {
  background: #fff;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2vh;
  border: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.choice-card.return .icon-circle {
  background: #166534;
}

.choice-card.return .choice-title {
  color: #14532d;
}

.choice-card.return .choice-desc {
  color: #888;
}

.choice-card.park {
  background: #14532d;
  color: #fff;
}

.choice-card.park .icon-circle {
  background: rgba(255, 255, 255, 0.1);
}

.choice-card.park .choice-title {
  color: #fff;
  font-size: 4vh;
  font-weight: 700;
}

.choice-card.park .choice-desc {
  color: rgba(255, 255, 255, 0.7);
  font-size: 2vh;
}

.icon-circle {
  width: 15vh;
  height: 15vh;
  border-radius: 50%;
  display: grid;
  place-items: center;
}

.choice-title {
  font-size: 4vh;
  font-weight: 700;
  color: #14532d;
}

.choice-desc {
  font-size: 2vh;
  color: #888;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.parking-modal {
  width: 60vw;
  background: #fff;
  border-radius: 24px;
  padding: 4vh;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}

.parking-modal.keyboard-up {
  transform: translateY(-15vh);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3vh;
}

.modal-header h2 {
  font-size: 3.5vh;
  margin: 0;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 2vh;
}

.field {
  position: relative;
}

.field input {
  width: 100%;
  height: 9vh;
  border-radius: 12px;
  border: 2px solid #ddd;
  padding: 0 2vw;
  font-size: 4vh;
  text-align: center;
}

.search-results {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 12px;
  max-height: 25vh;
  overflow-y: auto;
  margin-top: 1vh;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.search-item {
  padding: 2vh;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.search-item:last-child {
  border-bottom: none;
}

.search-item:active {
  background-color: #f5f5f5;
}

.car-num {
  font-size: 3vh;
  font-weight: 700;
  color: #14532d;
}

.loc-code {
  font-size: 2.5vh;
  color: #666;
}

.primary-btn {
  height: 9vh;
  background: #14532d;
  color: #fff;
  border-radius: 12px;
  font-size: 3.5vh;
  font-weight: 700;
  border: none;
  margin-top: 1vh;
}


.kiosk-toast :deep(.v-snackbar__wrapper) {
  background-color: #323232;
  min-width: 45vw;
  height: 7vh;
  border-radius: 12px;
  top: 2vh;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 3px solid var(--toast-accent, #ff5252);
}

.kiosk-toast :deep(.v-snackbar__content) {
  font-size: 2.5vh;
  font-family: var(--kiosk-font);
  color: #ffffff;
  white-space: nowrap;
  display: flex;
  align-items: center;
}
</style>
