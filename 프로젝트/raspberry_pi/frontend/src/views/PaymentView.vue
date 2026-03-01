<template>
  <v-app>
    <div class="payment-page">
      <header class="header-section">
        <div class="header-container">
          <div class="store-name">카터가든</div>
          <div class="header-actions">
            <div class="cart-info" @click="goToCart">
              <v-img :src="iconCart" alt="Cart" class="cart-icon-img"></v-img>
            </div>
          </div>
        </div>
      </header>

      <main class="main-section">
        <div class="main-container">
          <div class="coupon-section">
            <div class="section-header">
              <div class="section-title">
                <v-img :src="iconCoupon" alt="Coupon" class="title-icon coupon-icon"></v-img>
                <span class="title-text">사용 가능한 쿠폰</span>
              </div>
              <div class="section-description" v-if="userStore.userInfo?.user_id">
                쿠폰을 선택하여 할인을 적용하세요.
              </div>
            </div>

            <div class="coupon-scroll-wrapper">
              <div v-if="coupons.length > 0" class="coupon-grid">
                <div v-for="coupon in coupons" :key="coupon.coupon_id" class="coupon-item"
                  :class="{ selected: isSelected(coupon) }" @click="selectCoupon(coupon)">
                  <div class="coupon-radio">
                    <div class="radio-circle" :class="{ selected: isSelected(coupon) }"></div>
                  </div>
                  <div class="coupon-content">
                    <div class="coupon-name">{{ coupon.coupon_name }}</div>
                    <div class="coupon-condition">
                      만료일: {{ formatDate(coupon.expire_date) }}
                    </div>
                  </div>
                  <div class="coupon-discount">-{{ formatPrice(coupon.discount_amount) }}원</div>
                </div>
              </div>
              <div v-else class="no-coupon-message">
                사용 가능한 쿠폰이 없습니다.
              </div>
            </div>
          </div>

          <div class="payment-methods">
            <div class="payment-button" :class="{ active: paymentMethod === 'card' }" @click="paymentMethod = 'card'">
              <div class="payment-icon-wrapper">
                <v-img :src="iconCreditCard" alt="Credit Card" class="payment-icon"></v-img>
              </div>
              <div class="payment-name">신용카드</div>
              <div class="payment-description">할부 및 일시불 결제</div>
            </div>

            <div class="payment-button" :class="{ active: paymentMethod === 'mobile' }"
              @click="paymentMethod = 'mobile'">
              <div class="payment-icon-wrapper">
                <v-img :src="iconMobile" alt="Easy Pay" class="payment-icon"></v-img>
              </div>
              <div class="payment-name">간편결제</div>
              <div class="payment-description">카카오페이 / 토스페이</div>
            </div>

            <div class="payment-button" :class="{ active: paymentMethod === 'point' }" @click="paymentMethod = 'point'">
              <div class="payment-icon-wrapper">
                <v-img :src="iconPoint" alt="Point" class="payment-icon"></v-img>
              </div>
              <div class="payment-name">포인트 결제</div>
              <div class="payment-description">멤버십 포인트 사용</div>
            </div>
          </div>
        </div>
      </main>

      <div class="total-amount-section">
        <div class="final-row">
          <div class="total-label">최종 결제 금액</div>
          <div class="total-price">
            <span class="original-price-strikethrough" v-if="cartStore.discountAmount > 0">
              {{ formatPrice(cartStore.totalProductPrice) }}원
            </span>
            <span class="price-number">{{ formatPrice(cartStore.finalPrice) }}</span>
            <span class="price-unit">원</span>
          </div>
        </div>
      </div>

      <footer class="footer-section">
        <div class="footer-container">
          <v-btn class="footer-btn-back" variant="outlined" @click="goBack">
            <div class="footer-icon-wrapper">
              <v-img :src="iconArrowBack" alt="Back" class="footer-icon footer-icon-follow"></v-img>
            </div>
            <div class="footer-text">이전 화면</div>
          </v-btn>

          <v-btn class="footer-btn-cancel" @click="openConfirmDialog">
            <v-img :src="iconFinish" alt="Finish" class="footer-icon footer-icon-list"></v-img>
            <div class="footer-text">결제 및 쇼핑 종료</div>
          </v-btn>
        </div>
      </footer>

      <v-dialog v-model="confirmDialog" max-width="500" persistent>
        <v-card class="pa-6 text-center mono-dialog" style="border-radius: 24px;">
          <v-card-title class="text-h5 font-weight-bold">결제 확인</v-card-title>
          <v-card-text class="text-body-1 py-4">
            <div class="mb-2">
              결제 수단: <strong>{{ paymentMethodName }}</strong>
            </div>
            <div class="mb-4">
              총 <span class="font-weight-bold mono-highlight">{{ formatPrice(cartStore.finalPrice) }}원</span>을<br>
              결제하시겠습니까?
            </div>
            <div class="tag-notice-box mono-tag-box">
              결제가 완료되면<br>
              <strong>장바구니가 초기화</strong>됩니다.
            </div>
          </v-card-text>
          <v-card-actions class="justify-center gap-4">
            <v-btn variant="text" color="grey-darken-1" @click="confirmDialog = false" class="px-6"
              style="font-size: 1.2rem;">취소</v-btn>
            <v-btn variant="flat" color="#166534" @click="processPayment" class="px-8 mono-confirm-btn"
              style="font-size: 1.2rem; height: 50px;" :loading="isLoading">결제하기</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-snackbar v-model="snackbar.show" location="top" :timeout="3000" flat class="kiosk-toast"
        :style="snackbar.color === 'error' ? '--toast-accent: #ff5252' : '--toast-accent: #4caf50'">
        <div class="toast-content">
          <v-icon :icon="snackbar.color === 'error' ? 'mdi-alert-circle-outline' : 'mdi-check-circle-outline'"
            class="mr-2" size="small"></v-icon>
          {{ snackbar.text }}
        </div>
      </v-snackbar>
    </div>
  </v-app>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useCartStore } from '@/store/cart';
import { useUserStore } from '@/store/user';
import { getUserCoupons } from '@/api/couponApi';

// Icon Imports
import iconCart from '@/assets/Cart.png';
import iconCoupon from '@/assets/coupon.png';
import iconCreditCard from '@/assets/credit_card_payment.png';
import iconMobile from '@/assets/mobile_payment.png';
import iconPoint from '@/assets/point_payment.png';
import iconArrowBack from '@/assets/arrow_back.png';
import iconFinish from '@/assets/finish.png';

const router = useRouter();
const cartStore = useCartStore();
const userStore = useUserStore();

// State
const paymentMethod = ref('card');
const coupons = ref([]);
const confirmDialog = ref(false);
const isLoading = ref(false);
const snackbar = reactive({ show: false, text: '', color: 'success' });

// Computed
const paymentMethodName = computed(() => {
  switch (paymentMethod.value) {
    case 'card': return '신용카드';
    case 'mobile': return '간편결제';
    case 'point': return '포인트';
    default: return '';
  }
});

// Methods
const formatPrice = (price) => price.toLocaleString();

const formatDate = (dateStr) => {
  if (!dateStr) return '무제한';
  const date = new Date(dateStr);
  return date.toLocaleDateString();
};

const fetchCoupons = async () => {
  const userId = userStore.userInfo?.user_id;
  if (!userId) return;
  try {
    const data = await getUserCoupons(userId);
    coupons.value = (data.coupons || []).filter(c => !c.is_used);
  } catch (error) {
    console.error('Failed to fetch coupons:', error);
  }
};

const selectCoupon = (coupon) => {
  if (isSelected(coupon)) {
    cartStore.clearCoupon();
  } else {
    cartStore.applyCoupon(coupon);
  }
};

const isSelected = (coupon) => {
  return cartStore.selectedCoupon && cartStore.selectedCoupon.coupon_id === coupon.coupon_id;
};

const goBack = () => router.go(-1);
const goToCart = () => router.push('/cart');

const openConfirmDialog = () => {
  confirmDialog.value = true;
};

const handleSuccess = () => {
  snackbar.text = '결제가 성공적으로 완료되었습니다!';
  snackbar.color = 'success';
  snackbar.show = true;

  cartStore.clearCart();

  setTimeout(() => {
    router.push('/finish');
  }, 1000);
};

// 가상 결제 프로세스 (모든 결제 수단 통합)
const processPayment = () => {
  // 로딩 상태를 보여주고 싶지 않다면 isLoading 관련 코드를 빼도 무방합니다.
  isLoading.value = true;
  
  // 지연 시간 없이 즉시 실행
  isLoading.value = false;
  confirmDialog.value = false;
  handleSuccess();
};

onMounted(() => {
  fetchCoupons();
});
</script>

<style scoped>
/* 기존 스타일 그대로 유지 (불필요한 위젯 관련 스타일 제외) */
* {
  box-sizing: border-box;
}

.payment-page {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
  font-family: var(--kiosk-font);
  overflow: hidden;
  border: 1px solid #ddd;
}

.header-section {
  background-color: #ffffff;
  height: 10.67vh;
  padding: 0 1.56vw;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e5e7eb;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.store-name {
  font-size: 2.1vw;
  font-weight: 700;
  color: #166534;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1.95vw;
}

.cart-info {
  display: flex;
  align-items: center;
  gap: 0.78vw;
  cursor: pointer;
}

.cart-icon-img {
  width: 3.52vw;
  height: 7.33vh;
}

.main-section {
  flex: 1;
  padding: 2.0vh 1.56vw;
  overflow-y: auto;
}

.coupon-section {
  background-color: #ffffff;
  padding: 2.7vh 2.34vw;
  border-radius: 1.17vw;
  margin-bottom: 2.2vh;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2vh;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.78vw;
}

.title-icon {
  width: 2.34vw;
  height: 3vh;
}

.title-text {
  font-size: 1.8vw;
  font-weight: 700;
  color: #14532d;
}

.section-description {
  font-size: 1.3vw;
  color: #64748b;
}

.coupon-scroll-wrapper {
  max-height: 40vh;
  overflow-y: auto;
  padding-right: 0.39vw;
}

.coupon-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.2vw;
}

.coupon-item {
  display: flex;
  align-items: center;
  padding: 2.5vh 1.56vw;
  border: 2px solid #e5e7eb;
  border-radius: 0.78vw;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #ffffff;
}

.coupon-item.selected {
  border-color: #166534;
  background-color: #ecfdf3;
}

.coupon-radio {
  margin-right: 1.17vw;
}

.radio-circle {
  width: 1.5vw;
  aspect-ratio: 1/1;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  position: relative;
}

.radio-circle.selected {
  border-color: #166534;
  background-color: #166534;
}

.radio-circle.selected::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 0.6vw;
  aspect-ratio: 1/1;
  background-color: #ffffff;
  border-radius: 50%;
}

.coupon-content {
  flex: 1;
}

.coupon-name {
  font-size: 1.37vw;
  font-weight: 600;
  color: #166534;
}

.coupon-condition {
  font-size: 1.17vw;
  color: #6b7280;
}

.coupon-discount {
  font-size: 1.56vw;
  font-weight: 700;
  color: #166534;
  margin-left: 1.17vw;
}

.no-coupon-message {
  text-align: center;
  padding: 3vh 0;
  color: #9ca3af;
  font-size: 1.3vw;
}

.payment-methods {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.2vw;
}

.payment-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2.5vh 1.56vw;
  background-color: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 1.17vw;
  cursor: pointer;
  transition: all 0.2s;
}

.payment-button.active {
  border-color: #166534;
  background-color: #ecfdf3;
}

.payment-icon-wrapper {
  width: 7.5vw;
  aspect-ratio: 1/1;
  background-color: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.2vh;
}

.payment-icon {
  width: 2.73vw;
  height: 4.67vh;
}

.payment-name {
  font-size: 1.6vw;
  font-weight: 600;
  color: #166534;
  margin-bottom: 0.4vh;
}

.payment-description {
  font-size: 1.17vw;
  color: #6b7280;
}

.total-amount-section {
  background-color: #ffffff;
  border-top: 1px solid #e5e7eb;
  padding: 1.2vh 1.56vw;
  display: flex;
  align-items: center;
}

.final-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.total-label {
  font-size: 1.37vw;
  font-weight: 600;
  color: #374151;
}

.total-price {
  display: flex;
  align-items: baseline;
  gap: 0.78vw;
}

.original-price-strikethrough {
  color: #9ca3af;
  font-size: 1.56vw;
  text-decoration: line-through;
}

.price-number {
  font-size: 2.73vw;
  font-weight: 700;
  color: #166534;
}

.price-unit {
  font-size: 1.56vw;
  font-weight: 500;
  color: #166534;
}

.footer-section {
  background-color: #ffffff;
  border-top: 1px solid #166534;
  padding: 2.67vh 1.56vw;
  flex-shrink: 0;
}

.footer-container {
  display: flex;
  gap: 1.56vw;
  justify-content: center;
}

.footer-btn-back {
  all: unset;
  align-items: center;
  border: 1px solid #166534;
  border-radius: 16px;
  box-sizing: border-box;
  display: flex;
  gap: 0.78vw;
  justify-content: center;
  padding: 2.67vh 0px;
  min-height: 10.67vh;
  width: 47.75vw;
  cursor: pointer;
  background-color: white;
  text-transform: none;
  color: #14532d;
}

.footer-btn-cancel {
  all: unset;
  align-items: center;
  background-color: #166534;
  border-radius: 16px;
  box-sizing: border-box;
  display: flex;
  gap: 0.78vw;
  justify-content: center;
  padding: 2.67vh 0px;
  min-height: 10.67vh;
  width: 47.56vw;
  cursor: pointer;
  text-transform: none;
  color: #ffffff;
}

.footer-icon {
  display: block;
}

.footer-icon-follow {
  width: 2.34vw;
  height: 4vh;
}

.footer-icon-list {
  width: 2.34vw;
  height: 4vh;
  filter: brightness(0) invert(1);
}

.footer-text {
  font-size: 2.34vw;
  font-weight: 700;
  line-height: 5.33vh;
}

.footer-btn-back .footer-text {
  color: #14532d;
}

.footer-btn-cancel .footer-text {
  color: #ffffff;
}

.mono-dialog {
  background-color: #fff;
  color: #166534;
  border: 1px solid #e5e7eb;
}

.mono-tag-box {
  background-color: #f5f5f5;
  border: 1px dashed #166534;
  padding: 16px;
  border-radius: 12px;
}

.mono-highlight {
  color: #166534;
  font-size: 1.5rem;
}

.mono-confirm-btn {
  color: #fff;
  background-color: #166534;
  border-radius: 12px;
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
  border-bottom: 3px solid var(--toast-accent, #4caf50);
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