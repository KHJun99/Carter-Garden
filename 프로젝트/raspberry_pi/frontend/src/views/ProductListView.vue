<template>
  <v-app class="kiosk-app">
    <div class="d-flex flex-column fill-height bg-grey-lighten-5">

      <header class="d-flex align-center bg-white elevation-1 z-index-10 product-header page-gutter"
        style="height: 12vh; flex-shrink: 0;">

        <div class="brand-title text-no-wrap">
          카터가든
        </div>

        <div class="d-flex align-center search-area">
          <v-text-field ref="searchInput" v-model="searchQuery" placeholder="상품 이름을 입력하세요" variant="solo"
            bg-color="#ffffff" flat hide-details rounded="xl" class="search-input" prepend-inner-icon="mdi-magnify"
            @focus="showSearchKeyboard = true" @keyup.enter="searchProducts"></v-text-field>
          <v-btn color="#166534" class="ml-3 text-white font-weight-bold rounded-xl search-btn" elevation="0"
            @click="searchProducts">
            검색
          </v-btn>
        </div>

        <div class="d-flex flex-column align-center cart-section cursor-pointer" @click="goToCart">
          <v-badge :content="cartStore.cartQuantity" color="#16a34a" offset-x="6" offset-y="6">
            <v-icon style="font-size: 4.5vh;" color="#166534">mdi-cart-outline</v-icon>
          </v-badge>
          <span class="font-weight-bold mt-1 cart-label" style="font-size: 1.8vh;">장바구니</span>
        </div>
      </header>

      <div class="d-flex flex-grow-1 overflow-hidden">
        <aside class="bg-white border-e d-flex flex-column overflow-y-auto hide-scrollbar category-panel"
          style="width: 20vw; flex-shrink: 0;">
          <v-list bg-color="transparent" class="pa-0" density="compact">
            <v-list-item v-for="cat in categoryList" :key="cat.category_id" rounded="xl" class="mb-2"
              style="min-height: 7vh;"
              :class="selectedCategory === cat.category_id ? 'category-active' : 'category-inactive'"
              @click="filterByCategory(cat.category_id)">
              <v-list-item-title class="font-weight-bold text-center" style="font-size: 2.2vh;">
                {{ cat.category_name }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </aside>

        <main class="flex-grow-1 bg-grey-lighten-4 pa-4 overflow-y-auto hide-scrollbar d-flex flex-column">
          <div v-if="productList.length > 0" class="d-flex flex-column" style="gap: 1.5vh;">
            <v-card v-for="product in productList" :key="product.product_id" flat
              class="d-flex align-center pa-3 rounded-xl border" style="height: 16vh;">
              <v-img :src="getImageUrl(product)" cover class="rounded-lg bg-grey-lighten-2 mr-4 flex-grow-0"
                style="width: 12vh; height: 12vh;" loading="lazy" transition="fade-transition">
                <template v-slot:placeholder>
                  <div class="d-flex align-center justify-center fill-height bg-grey-lighten-3">
                    <v-progress-circular indeterminate color="#a7f3d0" size="24"></v-progress-circular>
                  </div>
                </template>
              </v-img>

              <div class="d-flex flex-column flex-grow-1 justify-center">
                <span class="font-weight-bold mb-1" style="font-size: 2.8vh;">{{ product.product_name }}</span>
                <span class="text-grey-darken-1" style="font-size: 2.2vh;">{{ formatPrice(product.price) }}</span>
              </div>

              <v-btn icon color="#166534" class="text-white" style="width: 7vh; height: 7vh;" elevation="0"
                @click="moveRobotToProduct(product)">
                <v-icon style="font-size: 3.5vh;">mdi-cart-arrow-down</v-icon>
              </v-btn>
            </v-card>
          </div>

          <div v-else class="flex-grow-1 d-flex flex-column align-center justify-center text-grey">
            <v-icon style="font-size: 10vh;" class="mb-4" color="#a7f3d0">mdi-store-search-outline</v-icon>
            <div style="font-size: 3vh; font-weight: 500;">검색된 상품이 없습니다.</div>
          </div>
        </main>

        <aside class="bg-white border-s d-flex flex-column overflow-y-auto hide-scrollbar recommendation-panel"
          style="width: 28vw; flex-shrink: 0;">
          <div class="font-weight-bold d-flex align-left mb-4" style="font-size: 2.4vh; color: #166534;">
            AI 추천 상품
          </div>

          <div v-if="cartStore.isLoadingRecommendation"
            class="flex-grow-1 d-flex flex-column align-center justify-center text-grey">
            <v-progress-circular indeterminate color="#16a34a" class="mb-4" size="50"></v-progress-circular>
            <div style="font-size: 2.2vh;">AI 추천 중...</div>
          </div>

          <v-card v-else-if="cartStore.recommendedProduct"
            class="rounded-xl border elevation-0 d-flex flex-column recommended-card"
            style="border-color: #E5E7EB; height: auto; max-height: 48vh;">
            <v-img v-if="getImageUrl(cartStore.recommendedProduct)" :src="getImageUrl(cartStore.recommendedProduct)"
              height="20vh" contain class="bg-white rounded-t-xl recommended-image" transition="fade-transition">
            </v-img>
            <div class="pa-4 bg-white d-flex flex-column">
              <div class="mb-4">
                <div class="font-weight-bold mb-1" style="font-size: 2.4vh; color: #166534;">
                  {{ cartStore.recommendedProduct.product_name }}
                </div>
                <div class="text-green-darken-2 font-weight-bold" style="font-size: 3vh;">
                  {{ formatPrice(cartStore.recommendedProduct.price) }}
                </div>
              </div>
              <v-btn block color="#166534" class="text-white font-weight-bold rounded-lg"
                style="height: 6.5vh; font-size: 2.2vh;" elevation="0"
                @click="moveRobotToProduct(cartStore.recommendedProduct)">
                담으러 가기
              </v-btn>
            </div>
          </v-card>
        </aside>
      </div>

      <virtual-keyboard :isActive="showSearchKeyboard" @input="handleSearchKeyboardInput"
        @done="showSearchKeyboard = false" @close="showSearchKeyboard = false" />

      <footer class="footer-section page-gutter">
        <div class="footer-container">
          <v-btn class="footer-btn-follow" variant="outlined" @click="startFollowMode">
            <div class="footer-btn-content">
              <v-img :src="iconToFollow" alt="Follow" class="footer-icon-follow"></v-img>
              <div class="footer-text-follow">따라가기 모드</div>
            </div>
          </v-btn>
          <v-btn class="footer-btn-list" @click="finishShopping">
            <div class="footer-btn-content">
              <v-img :src="iconFinish" alt="Finish" class="footer-icon-list"></v-img>
              <div class="footer-text-list">쇼핑 종료</div>
            </div>
          </v-btn>
        </div>
      </footer>
    </div>
  </v-app>
</template>


<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useCartStore } from '@/store/cart';
import { useNavigationStore } from '@/store/navigation'; // [추가]
import { getCategories } from '@/api/productApi';
import VirtualKeyboard from '@/components/common/VirtualKeyboard.vue';
import iconToFollow from '@/assets/ToFollow.png';
import iconFinish from '@/assets/finish.png';
import { getImageUrl } from '@/utils/imageUtils';
import rosManager from '@/api/rosManager';
import { applyVirtualKeyboardInput } from '@/utils/keyboardInput';

const router = useRouter();
const cartStore = useCartStore();
const navStore = useNavigationStore(); // [추가]

const searchQuery = ref('');
const selectedCategory = ref(0);
const showSearchKeyboard = ref(false);
const categoryList = ref([]);
const STORAGE_START = { code: 'STOR-001', x: 1.400, y: 1.46 };

const productList = computed(() => {
  return cartStore.getFilteredProducts(selectedCategory.value, searchQuery.value);
});

const loadCategories = async () => {
  try {
    const data = await getCategories();
    categoryList.value = [{ category_id: 0, category_name: '전체 보기' }, ...data];
  } catch (error) {
    console.error(error);
  }
};

const formatPrice = (price) => {
  return new Intl.NumberFormat('ko-KR').format(price) + '원';
};

const filterByCategory = (id) => {
  selectedCategory.value = id;
  searchQuery.value = '';
};

const goToCart = () => router.push({ name: 'cart' });

const handleSearchKeyboardInput = (key) => {
  if (key === 'Enter') {
    showSearchKeyboard.value = false;
    searchProducts();
  } else {
    searchQuery.value = applyVirtualKeyboardInput(searchQuery.value, key);
  }
};

const searchProducts = () => {
  if (searchQuery.value.trim()) {
    selectedCategory.value = 0;
  }
  showSearchKeyboard.value = false;
};

const moveRobotToProduct = async (product) => {
  // Nav2 웨이포인트 경로 전송 로직
  if (!navStore.mapLoaded) {
    await navStore.initMap();
  }

  const targetCode = product.location?.location_code;
  if (!targetCode) {
    console.error("상품 위치 정보가 없습니다.");
    return;
  }

  // 현재 위치 -> 목표 위치 경로 계산
  const hasCartItems = cartStore.cartItems.length > 0;
  const recentLocation = cartStore.lastAddedProductLocation;
  const startCode = hasCartItems && recentLocation?.code
    ? recentLocation.code
    : STORAGE_START.code;
  navStore.lastStartPose = hasCartItems && recentLocation?.code
    ? { code: recentLocation.code, x: recentLocation.x, y: recentLocation.y }
    : STORAGE_START;

  const payload = navStore.getNavigationPayload(startCode, targetCode);

  if (payload) {
    console.log(`Sending Navigation Payload: ${startCode} -> ${targetCode}`);
    rosManager.sendMode('NAV');
    rosManager.sendDestination(payload);

    // 논리적 현재 위치 업데이트
  } else {
    console.error("경로를 찾을 수 없습니다.");
  }

  router.push({
    name: 'guide',
    query: {
      from: 'products',
      name: product.product_name,
      code: targetCode,
      x: product.location?.pos_x || 0,
      y: product.location?.pos_y || 0
    }
  });
};

const addToCart = (product) => {
  cartStore.addProduct(product);
  moveRobotToProduct(product);
};

const startFollowMode = () => router.push({ name: 'follow' });
const finishShopping = () => router.push({ name: 'payment' });

onMounted(() => {
  loadCategories();
  if (cartStore.allProducts.length === 0) {
    cartStore.loadAllProducts();
  }
});
</script>


<style scoped>
.product-header {
  justify-content: space-between;
  gap: 1.56vw;
}

.brand-title{
  margin-left: 2.6vw;
  font-family: 'Cafe24 Ssurround', 'Black Han Sans', var(--kiosk-font), sans-serif;
  font-size: 4.3vh;
  font-weight: 700;
  letter-spacing: -1px;
  color: var(--kiosk-green-800);
  line-height: 1;
  text-shadow: 0 1px 0 rgba(0, 0, 0, 0.03);
}


.search-area {
  flex: 0 1 65vw;
  margin-left: 1.56vw;
  margin-right: 1.56vw;
}

.search-input {
  width: 100%;
}

.search-btn {
  height: 6.5vh;
  width: 8vw;
  font-size: 2.2vh;
}

.cart-section {
  min-width: 8vw;
}

.category-panel {
  padding: 2vh 1.56vw;
}

.recommendation-panel {
  padding: 2vh 1.56vw;
}

.cart-label {
  color: var(--kiosk-green-800);
}

.kiosk-app {
  font-family: var(--kiosk-font);
  user-select: none;
}

:deep(.v-text-field .v-field__input) {
  font-size: 2.4vh;
  min-height: 6.5vh;
  display: flex;
  align-items: center;
}

:deep(.search-input .v-field) {
  border: 2px solid var(--kiosk-green-700);
  background-color: #ffffff;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

.hide-scrollbar {
  scrollbar-width: none;
}

.category-active {
  background-color: var(--kiosk-green-800);
  color: #ffffff;
}

.category-inactive {
  color: var(--kiosk-muted);
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

.footer-btn-content {
  display: flex;
  align-items: center;
  gap: 0.78vw;
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

.recommended-image {
  padding: 1vh 0.8vw;
}
</style>
