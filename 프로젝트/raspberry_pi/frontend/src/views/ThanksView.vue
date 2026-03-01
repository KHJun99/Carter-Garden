<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNavigationStore } from '@/store/navigation';
import rosManager from '@/api/rosManager';
import { getLocationByCode } from '@/api/locationApi';
import { playSound } from '@/utils/audio';

const router = useRouter();
const navStore = useNavigationStore();
const description = ref('카트가 안전하게 반납 장소로 이동합니다.');

onMounted(() => {
  // 1. 오디오 재생
  playSound('audio/finish.wav');

  // 2. 로봇 상태 모니터링
  rosManager.onStatus(async (status) => {
    if (status === 'ARRIVED') {
      description.value = '반납이 완료되었습니다. 잠시 후 시작화면으로 돌아갑니다.';

      // 2초 대기 후 초기화 및 이동
      setTimeout(async () => {
        try {
          // 카트보관함(STOR-001) 위치 명시적 조회
          const storage = await getLocationByCode('STOR-001');

          if (storage) {
            // 로봇의 물리적 위치(AMCL)와 논리적 위치(Store)를 모두 저장소 위치로 초기화
            rosManager.sendInitialPose(storage.pos_x, storage.pos_y);

            console.log(`반납 완료: 현재 위치가 ${storage.location_code}로 초기화되었습니다.`);
          }
        } catch (error) {
          console.warn('초기 위치 재설정 실패:', error);
        }

        // 홈 화면으로 복귀
        router.push({ name: 'home' });
      }, 2000);
    }
  });
});
</script>

<template>
  <main class="thanks-page">
    <div class="thanks-card">
      <div class="icon-section">
        <v-icon size="12vh" color="#111">mdi-check-circle-outline</v-icon>
      </div>
      <h1 class="thanks-title">이용해주셔서 감사합니다</h1>
      <p class="thanks-desc">{{ description }}</p>
    </div>
  </main>
</template>

<style scoped>
.thanks-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  font-family: var(--kiosk-font);
  color: #14532d;
  text-align: center;
  overflow: hidden;
}

.thanks-card {
  width: 70vw;
  padding: 8vh 5vw;
  border-radius: 32px;
  background: #ffffff;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3vh;
}

.icon-section {
  margin-bottom: 1vh;
}

.thanks-title {
  margin: 0;
  font-size: 7vh;
  font-weight: 800;
  line-height: 1.2;
}

.thanks-desc {
  margin: 0;
  font-size: 3.5vh;
  font-weight: 500;
  color: #666666;
}

.thanks-card {
  animation: popIn 0.5s ease-out;
}

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>