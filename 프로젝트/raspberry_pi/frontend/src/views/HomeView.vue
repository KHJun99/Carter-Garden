<template>
  <main class="home-page">
    <header class="hero">
      <h1 class="main-logo">
        <span class="logo-accent">C</span>ARTER
        <span class="logo-accent">G</span>ARDEN
      </h1>
      <p class="tagline">쇼핑을 시작해보세요!</p>
    </header>

    <section class="choice-grid">
      <RouterLink class="choice-card member" to="/login">
        <span class="icon-circle" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <circle cx="12" cy="8" r="3.4" />
            <path d="M5.5 19.5c1.6-3.2 4.3-4.8 6.5-4.8s4.9 1.6 6.5 4.8" fill="none" stroke="currentColor"
              stroke-width="2" />
          </svg>
        </span>
        <span class="choice-label">회원</span>
      </RouterLink>

      <div class="choice-card guest" role="button" tabindex="0" @click="goProductsWithSound">
        <span class="icon-circle" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <circle cx="8" cy="9" r="2.6" />
            <circle cx="16" cy="9" r="2.6" />
            <path d="M3.5 19c1.2-2.6 3.4-4 5.5-4s4.3 1.4 5.5 4" fill="none" stroke="currentColor" stroke-width="2" />
            <path d="M10.5 19c1.2-2.6 3.4-4 5.5-4s4.3 1.4 5.5 4" fill="none" stroke="currentColor" stroke-width="2" />
          </svg>
        </span>
        <span class="choice-label">비회원</span>
      </div>
    </section>
  </main>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { playSound } from '@/utils/audio'

const router = useRouter()

const goProductsWithSound = () => {
  playSound('audio/start.wav')
  router.push('/register-yolo')
}
</script>


<style scoped>
.home-page {
  position: relative;
  height: 100vh;
  padding: 8vh 4vw;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7vh;
  background: #ffffff;
  font-family: var(--kiosk-font);
  color: var(--kiosk-green-900);
  overflow: hidden;
}

.hero {
  text-align: center;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.main-logo {
  margin: 0;
  font-size: 9vw;
  font-weight: 700;
  color: var(--kiosk-green-800);
  letter-spacing: -0.02em;
  line-height: 1.1;
  text-shadow: 2px 2px 4px rgba(46, 125, 50, 0.15);
}

.logo-accent {
  font-size: 10.5vw;
  color: var(--kiosk-green-900);
}

.tagline {
  margin-top: 2.5vh;
  font-size: 3.2vw;
  color: var(--kiosk-muted);
  font-weight: 500;
}

.choice-grid {
  width: 90vw;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4vw;
  z-index: 1;
}

.choice-card {
  height: 45vh;
  border-radius: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3vh;
  text-decoration: none;
  box-shadow: 0 18px 40px rgba(20, 83, 45, 0.12);
  border: 3px solid var(--kiosk-border);
  transition: transform 0.2s;
}

.choice-card:active {
  transform: scale(0.98);
}

.choice-card.member {
  background: #ffffff;
  color: var(--kiosk-green-900);
  border-color: var(--kiosk-green-800);
}

.choice-card.guest {
  background: var(--kiosk-green-800);
  color: #ffffff;
  border-color: var(--kiosk-green-800);
}

.icon-circle {
  width: 8vw;
  height: 8vw;
  background: rgba(22, 101, 52, 0.12);
  border-radius: 50%;
  display: grid;
  place-items: center;
}

.choice-card.guest .icon-circle {
  background: rgba(255, 255, 255, 0.2);
}

.icon-circle svg {
  width: 4vw;
  height: 4vw;
  stroke: currentColor;
  fill: currentColor;
}

.choice-label {
  font-size: 4.5vw;
  font-weight: 600;
}
</style>
