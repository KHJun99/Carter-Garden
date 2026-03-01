<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="500"
    persistent>
    <v-card class="pa-6 text-center mono-dialog" style="border-radius: 24px;">
      <v-card-title class="text-h5 font-weight-bold">결제 확인</v-card-title>
      <v-card-text class="text-body-1 py-4">
        <div class="mb-4">
          총 <span class="font-weight-bold mono-highlight">{{ formatPrice(totalPrice) }}원</span>을<br>
          결제하시겠습니까?
        </div>
        <div class="tag-notice-box mono-tag-box">
          결제가 완료되면<br>
          <strong>장바구니가 초기화</strong>됩니다.
        </div>
      </v-card-text>
      <v-card-actions class="justify-center gap-4">
        <v-btn variant="text" color="grey-darken-1" @click="$emit('cancel')" class="px-6" style="font-size: 1.2rem;">
          취소
        </v-btn>
        <v-btn variant="flat" color="#166534" @click="$emit('confirm')" class="px-8 mono-confirm-btn"
          style="font-size: 1.2rem; height: 50px;">
          결제하기
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  totalPrice: {
    type: Number,
    required: true
  }
});

defineEmits(['update:modelValue', 'confirm', 'cancel']);

const formatPrice = (price) => price.toLocaleString();
</script>

<style scoped>
.mono-dialog {
  background-color: #ffffff;
  color: #166534;
  border: 1px solid #e5e7eb;
  box-shadow: 0px 18px 40px -20px rgba(0, 0, 0, 0.35);
}

.mono-tag-box {
  background-color: #f5f5f5;
  border: 1px dashed #166534;
  color: #166534;
  padding: 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.mono-highlight {
  color: #166534;
  font-size: 1.5rem;
}

.mono-confirm-btn {
  color: #ffffff;
  background-color: #166534;
  border-radius: 12px;
}

.gap-4 {
  gap: 16px;
}
</style>
