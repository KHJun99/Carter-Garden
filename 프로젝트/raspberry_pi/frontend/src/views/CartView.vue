<template>
  <v-app>
    <div class="kiosk-container">
      <header class="header-section">
        <div class="header-content">
          <div class="title-group">
            <v-img :src="iconCart" alt="Cart" class="header-icon"></v-img>
            <h1 class="page-title">장바구니</h1>
          </div>
          <div class="header-user">
            {{ userName }}님
          </div>
        </div>
      </header>

      <main class="body-section">
        <section class="product-list-column">
          <div v-if="cartItems.length === 0" class="empty-cart-container">
            <div class="icon-circle">
              <v-img :src="iconEmptyCart" width="5vw" height="5vw" contain></v-img>
            </div>
            <div class="empty-text">장바구니가 비어있습니다</div>
          </div>
          <div v-else class="scroll-wrapper">
            <div v-for="item in cartItems" :key="item.id" class="product-card">
              <div class="card-left-group">
                <div class="product-img-box">
                  <v-img v-if="getImageUrl(item)" :src="getImageUrl(item)" class="rounded-lg" cover
                    alt="Product Image"></v-img>
                  <span v-else style="font-size: 2rem;">📷</span>
                </div>
                <div class="product-info">
                  <div class="product-name">{{ getItemName(item) }}</div>
                  <div class="product-price">{{ formatPrice(item.price) }}원</div>
                </div>
              </div>

              <div class="card-right-group">
                <div class="qty-display">{{ item.quantity }}개</div>
                <div class="item-total-display">{{ formatPrice(item.price * item.quantity) }}원</div>
                <v-btn icon variant="text" color="red-lighten-1" @click="confirmDelete(item)">
                  <v-icon size="28">mdi-delete-outline</v-icon>
                </v-btn>
              </div>
            </div>
          </div>
        </section>

        <aside class="payment-column">
          <div class="desktop-outer-wrapper">
            <v-card class="background-shadow" elevation="24">
              <div class="summary-row row-item-price">
                <div class="text-wrapper-label">상품 금액</div>
                <div class="text-wrapper-value">{{ formatPrice(totalPrice) }} 원</div>
              </div>
              <div class="summary-row row-discount">
                <div class="text-wrapper-label">할인 금액</div>
                <div class="text-wrapper-discount">- {{ formatPrice(discountAmount) }} 원</div>
              </div>
              <div class="horizontal-border">
                <div class="summary-row row-final">
                  <div class="text-wrapper-label-sm">최종 결제 금액</div>
                  <div class="paragraph-total">
                    <div class="element-total">{{ formatPrice(finalPrice) }}</div>
                    <div class="text-wrapper-unit">원</div>
                  </div>
                </div>
              </div>
              <div class="spacer-v"></div>
              <v-btn class="pay-btn-white" elevation="2" @click="goToPayment" :disabled="finalPrice <= 0">
                <div class="btn-content">
                  <v-img :src="iconToPurchase" alt="Pay" class="btn-icon-img"></v-img>
                  <span class="text-wrapper-btn">결제하기</span>
                </div>
              </v-btn>
              <div class="container-footer-notice">
                <p class="p-notice">포인트 적립은 결제 완료 후 진행됩니다.</p>
              </div>
            </v-card>
          </div>
        </aside>
      </main>

      <v-dialog v-model="deleteDialog" max-width="500" persistent>
        <v-card class="pa-6 text-center mono-dialog" style="border-radius: 24px;">
          <v-card-title class="text-h5 font-weight-bold">상품 제거</v-card-title>
          <v-card-text class="text-body-1 py-4">
            <span class="font-weight-bold mono-highlight">"{{ getItemName(selectedItem) }}"</span> 상품을 1개
            제외하시겠습니까?<br><br>
            <div class="tag-notice-box mono-tag-box">
              카트의 센서에 해당 상품을 <br><strong>다시 한번 태깅(RFID)</strong> 해주세요.<br>
              태깅이 확인되면 자동으로 삭제됩니다.
            </div>
          </v-card-text>
          <v-card-actions class="justify-center">
            <v-btn variant="flat" color="#166534" @click="cancelDelete" class="px-8 mono-cancel-btn">취소</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-snackbar v-model="snackbar.show" location="top" :timeout="2500" flat class="kiosk-toast"
        style="--toast-accent: #4caf50">
        <div class="toast-content">
          <v-icon icon="mdi-check-circle-outline" class="mr-2" size="small" color="success"></v-icon>
          {{ snackbar.text }}
        </div>
      </v-snackbar>

      <footer class="footer-section">
        <div class="footer-container">
          <v-btn class="footer-btn-follow" variant="outlined" @click="goToGuide">
            <div class="footer-btn-content">
              <v-img :src="iconToFollow" alt="Follow" class="footer-icon-follow"></v-img>
              <div class="footer-text-follow">따라가기 모드</div>
            </div>
          </v-btn>
          <v-btn class="footer-btn-list" @click="goToProducts">
            <div class="footer-btn-content">
              <v-img :src="iconToList" alt="List" class="footer-icon-list"></v-img>
              <div class="footer-text-list">상품 목록</div>
            </div>
          </v-btn>
        </div>
      </footer>
    </div>
  </v-app>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useCartStore } from '@/store/cart';
import { useUserStore } from '@/store/user';
import { getImageUrl } from '@/utils/imageUtils';

import iconCart from '@/assets/Cart.png';
import iconToPurchase from '@/assets/ToPurchase.png';
import iconToFollow from '@/assets/ToFollow.png';
import iconToList from '@/assets/ToList.png';
import iconEmptyCart from '@/assets/empty_cart.png';

const router = useRouter();
const cartStore = useCartStore();
const userStore = useUserStore();
const { cartItems, lastRfidEvent, discountAmount, finalPrice } = storeToRefs(cartStore);
const userName = computed(() => userStore.getUserName);

const deleteDialog = ref(false);
const selectedItem = ref(null);
const snackbar = reactive({ show: false, text: '' });

const totalPrice = computed(() => {
  const itemsSum = cartItems.value.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  return itemsSum;
});

const formatPrice = (price) => price.toLocaleString();

const getItemName = (item) => item?.product_name || item?.name || '';
const getItemTagId = (item) => item?.product_id ?? item?.id;

const confirmDelete = (item) => {
  selectedItem.value = item;
  cartStore.setRfidRemovalTarget(getItemTagId(item));
  deleteDialog.value = true;
};

const cancelDelete = () => {
  deleteDialog.value = false;
  selectedItem.value = null;
  cartStore.clearRfidRemovalTarget();
};

watch(lastRfidEvent, (event) => {
  if (!event || event.action !== 'removed') return;
  if (!deleteDialog.value || !selectedItem.value) return;
  const itemName = getItemName(selectedItem.value);
  const removedAll = event?.item?.removedAll;
  snackbar.text = removedAll
    ? `"${itemName}" 상품이 장바구니에서 삭제되었습니다.`
    : `"${itemName}" 수량이 1개 제외되었습니다.`;
  snackbar.show = true;
  deleteDialog.value = false;
  selectedItem.value = null;
}, { deep: true });

const goToPayment = () => router.push('/payment');
const goToGuide = () => router.push('/follow');
const goToProducts = () => router.push('/products');
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.kiosk-container {
  width: 100%;
  height: 100vh;
  background-color: #ffffff;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #ddd;
  font-family: var(--kiosk-font);
}

.header-section {
  height: 10.67vh;
  padding: 0 1.56vw;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
  background-color: #fff;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 1.56vw;
  width: 100%;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 0.78vw;
}

.header-icon {
  width: 3.52vw;
  height: 7.33vh;
}

.page-title {
  font-size: 2.15vw;
  font-weight: 700;
  color: #166534;
  margin: 0;
}

.header-user {
  margin-left: auto;
  font-size: 1.5vw;
  font-weight: 600;
  color: #166534;
  text-align: right;
  margin-right: 1.56vw;
}

.body-section {
  flex: 1;
  display: flex;
  overflow: hidden;
  background-color: #f5f5f5;
  padding: 0 1.56vw;
}

.product-list-column {
  flex: 70.7;
  padding: 0.39vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scroll-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 0.78vw 0.39vw;
  display: flex;
  flex-direction: column;
  gap: 1.56vw;
}

.scroll-wrapper::-webkit-scrollbar {
  width: 6px;
}

.scroll-wrapper::-webkit-scrollbar-thumb {
  background-color: #ccc;
  border-radius: 3px;
}

.product-card {
  background-color: #ffffff;
  border-radius: 24px;
  height: 17.33vh;
  padding: 2.34vw;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #e5e7eb;
}

.dummy {
  opacity: 0.6;
}

.card-left-group {
  display: flex;
  align-items: center;
  gap: 2.34vw;
}

.product-img-box {
  width: 7.81vw;
  height: 13.33vh;
  background-color: #e5e7eb;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.img-placeholder-icon {
  font-size: 2.34vw;
  color: #999;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 0.67vh;
}

.product-name {
  font-size: 2.34vw;
  font-weight: 600;
  color: #111111;
  line-height: 5.33vh;
}

.product-price {
  font-size: 1.73vw;
  font-weight: 400;
  color: #4b5563;
  line-height: 4.67vh;
}

.tag-notice-box {
  padding: 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.mono-tag-box {
  background-color: #f5f5f5;
  border: 1px dashed #166534;
  color: #166534;
}

.mono-highlight {
  color: #166534;
}

.mono-dialog {
  background-color: #ffffff;
  color: #166534;
  border: 1px solid #e5e7eb;
  box-shadow: 0px 18px 40px -20px rgba(0, 0, 0, 0.35);
}

.mono-cancel-btn {
  color: #ffffff;
  background-color: #166534;
  border-radius: 12px;
}

.card-right-group {
  display: flex;
  align-items: center;
  gap: 1.5vw;
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

.qty-display {
  font-size: 1.95vw;
  font-weight: 500;
  color: #4b5563;
  line-height: 4.67vh;
}

.item-total-display {
  font-size: 2.16vw;
  font-weight: 700;
  color: #166534;
  line-height: 5.33vh;
  min-width: 12.5vw;
  text-align: right;
}

.payment-column {
  flex: 29.3;
  background-color: #f3f4f6;
  border-left: 1px solid #e0e0e0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.desktop-outer-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
  padding: 1.83vh 0 42vh 0;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}

.background-shadow {
  display: flex;
  width: 25.39vw;
  height: auto;
  min-height: 46.67vh;
  padding: 3.33vh 0.98vw 1.67vh 0.98vw;
  flex-direction: column;
  align-items: center;
  background-color: #166534;
  border-radius: 12px;
  box-shadow: 0px 25px 50px -12px #00000040;
  overflow: hidden;
  position: relative;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  width: 23.44vw;
}

.row-item-price {
  height: 4.67vh;
  margin-bottom: 1.33vh;
}

.row-discount {
  height: 4.67vh;
  margin-bottom: 2.67vh;
}

.text-wrapper-label {
  color: #ffffff;
  font-size: 1.95vw;
  font-weight: 400;
  line-height: 4.67vh;
}

.text-wrapper-value {
  color: #ffffff;
  font-size: 1.85vw;
  font-weight: 400;
  line-height: 4.67vh;
}

.text-wrapper-discount {
  color: #f87171;
  font-size: 1.87vw;
  font-weight: 400;
  line-height: 4.67vh;
}

.horizontal-border {
  width: 23.44vw;
  border-top: 1px solid #3f3f46;
  padding-top: 2.67vh;
  margin-bottom: 3.33vh;
  position: relative;
}

.row-final {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.text-wrapper-label-sm {
  color: #ffffff;
  font-size: 1.76vw;
  font-weight: 400;
  line-height: 4.67vh;
}

.paragraph-total {
  display: flex;
  align-items: flex-end;
}

.element-total {
  color: #ffffff;
  font-size: 2.34vw;
  font-weight: 700;
  letter-spacing: -1.2px;
}

.text-wrapper-unit {
  color: #ffffff;
  font-size: 1.95vw;
  font-weight: 400;
  letter-spacing: -1.2px;
  line-height: 5.33vh;
  margin-left: 0.2vw;
}

.spacer-v {
  height: 1.33vh;
}

.pay-btn-white {
  all: unset;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0px 8px 10px -6px #0000001a, 0px 20px 25px -5px #0000001a;
  box-sizing: border-box;
  width: 23.44vw;
  height: 10vh;
  margin-bottom: 2vh;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-transform: none;
}

.pay-btn-white:disabled {
  background-color: #e5e7eb;
  box-shadow: none;
  cursor: not-allowed;
  opacity: 0.6;
}

.pay-btn-white:disabled .text-wrapper-btn {
  color: #9ca3af;
}

.pay-btn-white:disabled .btn-icon-img {
  filter: grayscale(1);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 1.17vw;
}

.btn-icon-img {
  width: 2.73vw;
  height: 4.67vh;
}

.text-wrapper-btn {
  color: #166534;
  font-size: 1.95vw;
  font-weight: 900;
  line-height: 5.33vh;
}

.container-footer-notice {
  width: 23.44vw;
  text-align: left;
}

.p-notice {
  color: #ffffff;
  font-size: 1.17vw;
  font-weight: 400;
  line-height: 3.33vh;
  margin: 0;
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

.empty-cart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2vh;
  height: 100%;
}

.icon-circle {
  width: 8vw;
  height: 8vw;
  background-color: #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-text {
  font-size: 2vw;
  color: #6b7280;
  font-weight: 600;
}
</style>
