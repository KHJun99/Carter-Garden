<template>
  <v-app class="kiosk-app">
    <div class="d-flex flex-column fill-height bg-grey-lighten-5">
      <div class="d-flex flex-grow-1 overflow-hidden page-gutter guide-main">
        <section class="panel info-panel">
          <div class="status">
            <p class="status-line">{{ statusText }}</p>
          </div>
          <div class="icon-wrap" aria-hidden="true">
            <img :src="iconSrc" alt="icon" class="icon-image" />
          </div>
          <div class="destination">
            <p class="dest-title">{{ destinationName }}</p>
            <p class="dest-code">{{ destinationCode }}</p>
          </div>
        </section>

        <section class="panel map-panel" aria-label="지도">
          <div class="map-body" ref="mapContainer">
            <canvas ref="mapCanvas" class="map-canvas"></canvas>
          </div>
        </section>
      </div>

      <footer class="footer-section">
        <div class="footer-container">
          <v-btn class="footer-btn-follow" variant="outlined" @click="goBack">
            <div class="footer-btn-content">
              <div class="footer-icon-wrapper">
                <v-img :src="locationIcon" alt="location icon" class="footer-icon-follow"></v-img>
              </div>
              <div class="footer-text-follow">목적지 변경</div>
            </div>
          </v-btn>

          <v-btn class="footer-btn-list" @click="togglePause">
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
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import moveIcon from '@/assets/move.png'
import pauseIcon from '@/assets/Stop.png'
import playIcon from '@/assets/play.png'
import locationIcon from '@/assets/location.png'
import martMapImg from '@/assets/mart_high_res.png'
import rosManager from '@/api/rosManager'
import { MAP_INFO } from '@/config'
import { useNavigationStore } from '@/store/navigation'
import * as mapRenderer from '@/utils/mapRenderer'

const route = useRoute()
const router = useRouter()
const navStore = useNavigationStore()
const isPaused = ref(false)
const STORAGE_START = { code: 'STOR-001', x: 1.400, y: 1.46 }

const mapCanvas = ref(null)
const mapContainer = ref(null)
const robotPath = ref([])
const currentPose = ref({
  x: navStore.lastStartPose?.x ?? STORAGE_START.x,
  y: navStore.lastStartPose?.y ?? STORAGE_START.y
})
const mapImage = new Image()
let imageLoaded = false

// Map adjustment settings
const mapConfig = {
  zoom: 1.3,       // 130% 확대
  offsetX: -0.25,  // 왼쪽으로 25% 이동
  offsetY: -0.165  // 위쪽으로 16.5% 이동
}

mapImage.src = martMapImg
mapImage.onload = () => {
  imageLoaded = true
  drawMap()
}

// Waypoints from store (Dijkstra path)
const waypoints = computed(() => navStore.plannedWaypoints || [])

const drawMap = () => {
  if (!imageLoaded || !mapCanvas.value) return
  const canvas = mapCanvas.value
  const ctx = canvas.getContext('2d')

  const container = mapContainer.value
  if (container) {
    canvas.width = container.clientWidth
    canvas.height = container.clientHeight
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 1. Draw Background
  mapRenderer.drawBackground(ctx, mapImage, canvas, mapConfig)

  // 2. Draw Planned Path
  mapRenderer.drawPath(ctx, waypoints.value, canvas, mapImage, mapConfig, {
    color: 'rgba(59, 130, 246, 0.4)',
    lineWidth: 4,
    dashed: [10, 8]
  })

  // 3. Draw Traveled Path
  mapRenderer.drawPath(ctx, robotPath.value, canvas, mapImage, mapConfig, {
    color: '#22C55E',
    lineWidth: 6
  })

  // 4. Draw Destination
  const destX = parseFloat(route.query.x || 0)
  const destY = parseFloat(route.query.y || 0)
  mapRenderer.drawMarker(ctx, destX, destY, canvas, mapImage, mapConfig, {
    color: '#3B82F6',
    radius: 12,
    strokeColor: 'white',
    strokeWidth: 3
  })

  // 5. Draw Robot Position
  mapRenderer.drawMarker(ctx, currentPose.value.x, currentPose.value.y, canvas, mapImage, mapConfig, {
    color: '#EF4444',
    radius: 10,
    strokeColor: 'white',
    strokeWidth: 2
  })
}

onMounted(() => {
  currentPose.value = {
    x: navStore.lastStartPose?.x ?? STORAGE_START.x,
    y: navStore.lastStartPose?.y ?? STORAGE_START.y
  }

  rosManager.onPoseUpdate((pose) => {
    currentPose.value = { x: pose.x, y: pose.y }
    // Only add to path if moved significantly to reduce points
    const lastPoint = robotPath.value[robotPath.value.length - 1]
    if (!lastPoint || Math.hypot(lastPoint.x - pose.x, lastPoint.y - pose.y) > 0.05) {
      robotPath.value.push({ x: pose.x, y: pose.y })
    }
    drawMap()
  })

  // Initial draw
  if (imageLoaded) drawMap()

  // Handle window resize to keep map responsive if needed
  window.addEventListener('resize', drawMap)
})

onUnmounted(() => {
  window.removeEventListener('resize', drawMap)
  rosManager.onPoseUpdate(null) // Unsubscribe
})

const source = computed(() => {
  const querySource = String(route.query.from || '')
  if (querySource === 'finish' || querySource === 'products') {
    return querySource
  }

  const historyBack = router.options.history.state.back || ''
  if (historyBack.includes('/finish')) {
    return 'finish'
  }
  if (historyBack.includes('/products')) {
    return 'products'
  }

  return 'products'
})

const statusText = computed(() =>
  source.value === 'finish' ? '주차 위치로 이동 중' : '물건 탐색 중'
)

const destinationName = computed(() => {
  if (source.value === 'finish') return '주차장';
  return route.query.name || '알 수 없는 목적지';
});

const destinationCode = computed(() => {
  if (source.value === 'finish') return route.query.code || 'PARK-001';
  return route.query.code || '-';
});

const destX = computed(() => route.query.x || 0);
const destY = computed(() => route.query.y || 0);

const pauseLabel = computed(() =>
  isPaused.value ? '주행 시작' : '일시 정지'
)

const iconSrc = computed(() => moveIcon) // Assuming move.png for exploration

const btnIconSrc = computed(() =>
  isPaused.value ? playIcon : pauseIcon
)

const goBack = () => {
  router.push(source.value === 'finish' ? '/finish' : '/products')
}

const togglePause = () => {
  isPaused.value = !isPaused.value
  // 로봇에게 정지/재개 명령 전송
  const command = isPaused.value ? 'STOP' : 'RESUME';
  rosManager.sendMode(command);
}
</script>

<style scoped>
.kiosk-app {
  font-family: var(--kiosk-font);
  user-select: none;
}

.panel {
  background: #ffffff;
  margin: 0;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  border: 1px solid #ececec;
  display: flex;
  flex: 0 0 47.5vw;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.guide-main {
  justify-content: center;
  align-items: stretch;
  gap: 1.56vw;
}

.info-panel {
  gap: 3.33vh;
  padding: 3.33vh;
}

.map-panel {
  padding: 3.33vh;
}

.map-body {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  background: #f9fafc;
  border-radius: 15px;
  border: 1px solid #eef0f3;
  overflow: hidden;
}

.map-canvas {
  max-width: 100%;
  max-height: 100%;
  display: block;
}

.status {
  font-size: 5.33vh;
  font-weight: 600;
  color: var(--kiosk-green-800);
}

.icon-wrap {
  width: 23.33vh;
  height: 23.33vh;
  border-radius: 50%;
  background: var(--kiosk-green-800);
  display: grid;
  place-items: center;
}

.icon-image {
  width: 13.33vh;
  height: 13.33vh;
}

.destination {
  color: var(--kiosk-green-800);
  text-align: center;
}

.dest-title {
  font-size: 4vh;
  margin: 0;
}

.dest-code {
  font-size: 5vh;
  margin: 1.67vh 0 0;
}

.footer-section {
  align-items: flex-start;
  background-color: #ffffff;
  border-top: 1px solid #166534;
  display: flex;
  flex-direction: column;
  padding: 2.67vh 1.56vw;
  position: relative;
  width: 100%;
  flex-shrink: 0;
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
  all: unset;
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
}

.footer-text-follow {
  color: #14532d;
  font-size: 2.34vw;
  font-weight: 700;
  line-height: 5.33vh;
}

.footer-btn-list {
  all: unset;
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
