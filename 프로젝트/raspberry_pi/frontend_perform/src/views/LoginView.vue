<template>
  <v-app>
    <main class="login-page">
      <header class="hero">
        <h1 class="tagline">회원 로그인</h1>
      </header>

      <section :class="['login-card', { 'keyboard-up': showKeyboard }]" aria-label="회원 로그인">
        <label class="field">
          <span class="field-label">아이디</span>
          <input ref="usernameInput" type="text" placeholder="아이디를 입력하세요" v-model="username"
            @focus="focusedInput = 'username'; showKeyboard = true" />
        </label>

        <label class="field">
          <span class="field-label">비밀번호</span>
          <input ref="passwordInput" type="password" placeholder="비밀번호를 입력하세요" v-model="password" class="password-input"
            @focus="focusedInput = 'password'; showKeyboard = true" />
        </label>

        <button class="primary-btn" type="button" @click="handleLogin">로그인</button>
        <button class="secondary-btn" type="button" @click="goToProducts">비회원으로 계속하기</button>
      </section>

      <div v-if="showKeyboard" class="keyboard-container">
        <virtual-keyboard :isActive="showKeyboard" @input="handleKeyboardInput" @done="showKeyboard = false"
          @close="showKeyboard = false" />
      </div>

      <v-snackbar v-model="snackbar.show" location="top" :timeout="3000" flat class="kiosk-toast">
        <div class="toast-content">
          <v-icon icon="mdi-alert-circle-outline" class="mr-2" size="small"></v-icon>
          {{ snackbar.text }}
        </div>
      </v-snackbar>
    </main>
  </v-app>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import VirtualKeyboard from '@/components/common/VirtualKeyboard.vue'
import { playSound } from '@/utils/audio'
import { applyVirtualKeyboardInput } from '@/utils/keyboardInput'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const showKeyboard = ref(false)
const focusedInput = ref('')

const snackbar = reactive({
  show: false,
  text: '',
  color: ''
})

const handleKeyboardInput = (key) => {
  if (focusedInput.value === 'username') {
    username.value = applyVirtualKeyboardInput(username.value, key)
  } else if (focusedInput.value === 'password') {
    password.value = applyVirtualKeyboardInput(password.value, key)
  }
}

const goToProducts = () => {
  playSound('audio/start.wav')
  router.push('/register-yolo')
}

const handleLogin = async () => {
  const isUsernameEmpty = !username.value.trim()
  const isPasswordEmpty = !password.value.trim()

  if (isUsernameEmpty || isPasswordEmpty) {
    snackbar.text = '아이디와 비밀번호를 모두 입력해주세요.'
    snackbar.show = true
    return
  }

  try {
    await userStore.login(username.value, password.value)
    playSound('audio/start.wav')
    router.push('/register-yolo')
  } catch (error) {
    snackbar.text = '아이디 또는 비밀번호가 일치하지 않습니다.'
    snackbar.show = true
  }
}
</script>

<style scoped>
.password-input::placeholder {
  letter-spacing: normal;
  font-size: 2.5vh;
  color: #6b7280;
}

input::placeholder {
  letter-spacing: normal;
  font-size: 2.5vh;
  color: #6b7280;
}

.password-input {
  letter-spacing: 0.3em;
}

.login-page {
  height: 100vh;
  padding-top: 7vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #ffffff;
  font-family: var(--kiosk-font);
  overflow: hidden;
}

.hero {
  margin-bottom: 3vh;
}

.tagline {
  font-size: 5vh;
  font-weight: 800;
  color: var(--kiosk-green-900);
}

.login-card {
  width: 50vw;
  background: #ffffff;
  border-radius: 28px;
  padding: 4vh 3vw;
  display: flex;
  flex-direction: column;
  gap: 2vh;
  box-shadow: 0 18px 40px rgba(20, 83, 45, 0.12);
  border: 2px solid #166534;
  transition: transform 0.3s ease;
}

.login-card.keyboard-up {
  transform: translateY(-12vh);
}

.field {
  display: flex;
  flex-direction:
    column;
  gap: 1vh;
}

.field-label {
  font-size: 2.5vh;
  font-weight: 600;
  color: var(--kiosk-green-900);
}

.field input {
  height: 7.5vh;
  border-radius: 14px;
  border: 1px solid #166534;
  padding: 0 2vw;
  font-size: 2.8vh;
  background: #f6fdf8;
  color: var(--kiosk-green-900);
  box-shadow: inset 0 0 0 1px rgba(22, 101, 52, 0.08);
}

.field input:focus {
  outline: none;
  border-color: var(--kiosk-green-800);
  box-shadow: 0 0 0 3px rgba(22, 101, 52, 0.18);
}

.primary-btn,
.secondary-btn {
  height: 8.5vh;
  border-radius: 16px;
  font-size: 3vh;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.primary-btn {
  background: var(--kiosk-green-800);
  color: #ffffff;
  margin-top: 1vh;
}

.secondary-btn {
  background: #ffffff;
  border: 2px solid #166534;
  color: var(--kiosk-green-900);
}

.keyboard-container {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100vw;
  z-index: 1000;
}

.kiosk-toast :deep(.v-snackbar__wrapper) {
  background-color: var(--kiosk-green-900);
  min-width: 45vw;
  height: 7vh;
  border-radius: 12px;
  top: 2vh;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 3px solid var(--kiosk-green-600);
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
