<template>
  <div v-if="isActive" class="android-keyboard-overlay" @click="closeKeyboard">
    <div class="android-keyboard" @click.stop>
      <div class="keyboard-row">
        <button v-for="num in numbers" :key="num" @mousedown.prevent="inputKey(num)" class="key-btn">
          {{ num }}
        </button>
      </div>

      <div class="keyboard-row">
        <button v-for="key in currentLayout[0]" :key="key" @mousedown.prevent="inputKey(getDisplayKey(key))"
          class="key-btn">
          {{ getDisplayKey(key) }}
        </button>
      </div>

      <div class="keyboard-row">
        <button v-for="key in currentLayout[1]" :key="key" @mousedown.prevent="inputKey(getDisplayKey(key))"
          class="key-btn">
          {{ getDisplayKey(key) }}
        </button>
      </div>

      <div class="keyboard-row">
        <button @mousedown.prevent="toggleShift" class="key-btn special-key shift" :class="{ active: isShift }">
          <svg viewBox="0 0 24 24" width="22" height="22" :fill="isShift ? '#202124' : '#5f6368'">
            <path d="M12 4.5l-9 9h6V19h6v-5.5h6l-9-9z" />
          </svg>
        </button>

        <button v-for="key in currentLayout[2]" :key="key" @mousedown.prevent="inputKey(getDisplayKey(key))"
          class="key-btn">
          {{ getDisplayKey(key) }}
        </button>

        <button @mousedown.prevent="backspace" class="key-btn special-key backspace">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="#5f6368">
            <path
              d="M22 3H7c-.69 0-1.23.35-1.59.88L0 12l5.41 8.11c.36.53.9.89 1.59.89h15c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-3 12.59L17.59 17 14 13.41 10.41 17 9 15.59 12.59 12 9 8.41 10.41 7 14 10.59 17.59 7 19 8.41 15.41 12 19 15.59z" />
          </svg>
        </button>
      </div>

      <div class="keyboard-row control-row">
        <button @mousedown.prevent="toggleLayout" class="key-btn special-key mode-change">
          !#1
        </button>
        <button @mousedown.prevent="changeLanguage" class="key-btn special-key lang-change">
          {{ isKorean ? '한/영' : 'En' }}
        </button>
        <button @mousedown.prevent="inputKey(',')" class="key-btn"> , </button>
        <button @mousedown.prevent="inputKey(' ')" class="key-btn space">
          <div class="space-bar-line"></div>
        </button>
        <button @mousedown.prevent="inputKey('.')" class="key-btn"> . </button>

        <button @mousedown.prevent="done" class="key-btn done-btn">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="#5f6368">
            <path d="M16.01 11H4v2h12.01v3L20 12l-3.99-4v3z" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue';

const props = defineProps({
  isActive: Boolean,
});

const emit = defineEmits(['input', 'done', 'close']);

const isKorean = ref(true);
const isShift = ref(false);
const isNumberMode = ref(false);

const numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];

const shiftMap = {
  'ㅂ': 'ㅃ', 'ㅈ': 'ㅉ', 'ㄷ': 'ㄸ', 'ㄱ': 'ㄲ', 'ㅅ': 'ㅆ',
  'ㅐ': 'ㅒ', 'ㅔ': 'ㅖ'
};

const layouts = {
  kor: [
    ['ㅂ', 'ㅈ', 'ㄷ', 'ㄱ', 'ㅅ', 'ㅛ', 'ㅕ', 'ㅑ', 'ㅐ', 'ㅔ'],
    ['ㅁ', 'ㄴ', 'ㅇ', 'ㄹ', 'ㅎ', 'ㅗ', 'ㅓ', 'ㅏ', 'ㅣ'],
    ['ㅋ', 'ㅌ', 'ㅊ', 'ㅍ', 'ㅠ', 'ㅜ', 'ㅡ']
  ],
  eng: [
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm']
  ],
  num: [
    ['+', '×', '÷', '=', '/', '_', '<', '>', '[', ']'],
    ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
    ['-', "'", '"', ':', ';', ',', '?']
  ]
};

const currentLayout = computed(() => {
  if (isNumberMode.value) return layouts.num;
  return isKorean.value ? layouts.kor : layouts.eng;
});

const getDisplayKey = (key) => {
  if (isNumberMode.value) return key;
  if (isShift.value) {
    if (isKorean.value) return shiftMap[key] || key;
    return key.toUpperCase();
  }
  return key;
};

const inputKey = (key) => {
  emit('input', key);
  if (isShift.value) isShift.value = false;
};

const backspace = () => emit('input', 'Backspace');
const toggleShift = () => (isShift.value = !isShift.value);
const toggleLayout = () => (isNumberMode.value = !isNumberMode.value);
const changeLanguage = () => {
  isKorean.value = !isKorean.value;
  isNumberMode.value = false;
};
const done = () => emit('done');
const closeKeyboard = () => emit('close');
</script>

<style scoped>
.android-keyboard-overlay {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  top: 0;
  background: transparent;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 9999;
  pointer-events: auto;
}

.android-keyboard {
  background: #f1f3f4;
  width: 60vw;
  padding: 10px 8px 15px 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -3px 15px rgba(0, 0, 0, 0.1);
  pointer-events: auto;
  font-family: var(--kiosk-font);
}

.keyboard-row {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.key-btn {
  flex: 1;
  height: 6.5vh;
  background: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 2.2vh;
  font-weight: 500;
  color: #202124;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  user-select: none;
}

.key-btn:active {
  background: #e8eaed;
}

.special-key,
.done-btn {
  background: #dadce0;
  flex: 1.4;
}

.backspace,
.shift {
  flex: 1.5;
}

.space {
  flex: 4;
}

.space-bar-line {
  width: 35%;
  height: 2px;
  background: #9aa0a6;
  border-radius: 2px;
  margin-top: 18px;
}

.mode-change,
.lang-change {
  font-size: 1.8vh;
  color: #5f6368;
}

.shift.active {
  background: #ffffff;
  box-shadow: inset 0 0 0 2px #202124;
}
</style>