import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { getProducts, getRecommendation } from '@/api/productApi';
import { API_URL } from '@/config';

const CART_STORAGE_KEY = 'smart-cart-items';

const initialProducts = [
  {
    id: 1,
    product_id: 101,
    product_name: 'Cola 1.5L',
    name: 'Cola 1.5L',
    price: 3200,
    image_url: '',
    location: { location_code: 'A1', pos_x: 1, pos_y: 1 }
  },
  {
    id: 2,
    product_id: 102,
    product_name: 'Water 2L',
    name: 'Water 2L',
    price: 1000,
    image_url: '',
    location: { location_code: 'A2', pos_x: 2, pos_y: 1 }
  },
  {
    id: 3,
    product_id: 103,
    product_name: 'Instant Ramen',
    name: 'Instant Ramen',
    price: 1200,
    image_url: '',
    location: { location_code: 'B1', pos_x: 1, pos_y: 2 }
  },
  {
    id: 4,
    product_id: 104,
    product_name: 'Curry 3-Minute',
    name: 'Curry 3-Minute',
    price: 2000,
    image_url: '',
    location: { location_code: 'B2', pos_x: 2, pos_y: 2 }
  }
];

export const useCartStore = defineStore('cart', () => {
  const allProducts = ref(initialProducts);
  const cartItems = ref([]);
  
  const selectedCoupon = ref(null); // 선택된 쿠폰

  const cartCount = computed(() => cartItems.value.length);
  const cartQuantity = computed(() => {
    return cartItems.value.reduce((sum, item) => sum + (item.quantity || 0), 0);
  });
  
  // 총 상품 금액
  const totalProductPrice = computed(() => {
    return cartItems.value.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  });

  // 할인 금액
  const discountAmount = computed(() => {
    return selectedCoupon.value ? selectedCoupon.value.discount_amount : 0;
  });

  // 최종 결제 금액 (0원 미만으로 내려가지 않음)
  const finalPrice = computed(() => {
    const total = totalProductPrice.value - discountAmount.value;
    return total > 0 ? total : 0;
  });

  const recommendedProduct = ref(null);
  const isLoadingRecommendation = ref(false);
  const rfidRemovalTargetId = ref(null);
  const lastRfidEvent = ref(null);
  const lastAddedProductLocation = ref(null);

  const loadCartFromStorage = () => {
    try {
      const raw = localStorage.getItem(CART_STORAGE_KEY);
      if (!raw) return;
      const storedItems = JSON.parse(raw);
      if (Array.isArray(storedItems) && storedItems.length > 0) {
        cartItems.value = storedItems;
      }
    } catch (error) {
      console.warn('Cart storage load failed:', error);
    }
  };

  const preloadImages = () => {
    if (allProducts.value.length === 0) return;
    const baseUrl = (API_URL || '').replace(/\/api\/?$/, '');

    allProducts.value.forEach(product => {
      if (product.image_url) {
        const img = new Image();
        let path = product.image_url.replace(/^\/?static\//, '');
        img.src = `${baseUrl}/static/images/${path}`;
      }
    });
  };

  const loadAllProducts = async () => {
    try {
      const data = await getProducts({});
      const products = data?.products || data || [];

      if (Array.isArray(products) && products.length > 0) {
        allProducts.value = products;
        console.log(`[CartStore] Loaded ${products.length} products.`);
        preloadImages();
      }
    } catch (error) {
      console.error('Product list fetch failed:', error);
    }
  };

  const findProductByTagId = (productId) => {
    const normalizedId = String(productId);
    return allProducts.value.find((product) => {
      const candidateId = product.product_id ?? product.id;
      return String(candidateId) === normalizedId;
    });
  };

  const getFilteredProducts = (categoryId, keyword) => {
    let result = allProducts.value;

    if (keyword) {
      const lowerKw = keyword.toLowerCase();
      result = result.filter(p =>
        p.product_name.toLowerCase().includes(lowerKw) ||
        (p.description && p.description.toLowerCase().includes(lowerKw))
      );
    } else if (categoryId && categoryId !== 0) {
      result = result.filter(p => p.category_id === categoryId);
    }
    return result;
  };

  const normalizeCartItem = (product) => ({
    ...product,
    name: product.product_name || product.name,
    product_id: product.product_id ?? product.id,
    quantity: 1
  });

  function addProductByLocalId(productId) {
    const product = findProductByTagId(productId);
    if (product) {
      const normalizedId = product.product_id ?? product.id;
      const existing = cartItems.value.find(
        (item) => String(item.product_id ?? item.id) === String(normalizedId)
      );
      if (existing) {
        existing.quantity += 1;
      } else {
        cartItems.value.push(normalizeCartItem(product));
      }
      if (product.location?.location_code) {
        lastAddedProductLocation.value = {
          code: product.location.location_code,
          x: product.location.pos_x,
          y: product.location.pos_y,
          name: product.product_name || product.name || ''
        };
      }
      return true;
    }
    return false;
  }

  const addProduct = (product) => {
    if (!product) return false;
    const normalizedId = product.product_id ?? product.id;
    if (!normalizedId) return false;
    const existing = cartItems.value.find(
      (item) => String(item.product_id ?? item.id) === String(normalizedId)
    );
    if (existing) {
      existing.quantity += 1;
    } else {
      cartItems.value.push(normalizeCartItem(product));
    }
    if (product.location?.location_code) {
      lastAddedProductLocation.value = {
        code: product.location.location_code,
        x: product.location.pos_x,
        y: product.location.pos_y,
        name: product.product_name || product.name || ''
      };
    }
    return true;
  };

  const removeOneByTagId = (productId) => {
    const normalizedId = String(productId);
    const targetIndex = cartItems.value.findIndex(
      (item) => String(item.product_id ?? item.id) === normalizedId
    );
    if (targetIndex === -1) return null;
    const targetItem = cartItems.value[targetIndex];
    const removedAll = targetItem.quantity <= 1;
    if (removedAll) {
      cartItems.value.splice(targetIndex, 1);
    } else {
      targetItem.quantity -= 1;
    }
    return { item: targetItem, removedAll };
  };

  const setRfidRemovalTarget = (productId) => {
    rfidRemovalTargetId.value = productId ? String(productId) : null;
  };

  const clearRfidRemovalTarget = () => {
    rfidRemovalTargetId.value = null;
  };

  const handleRfidScan = (productId) => {
    const normalizedId = String(productId);
    if (rfidRemovalTargetId.value) {
      if (normalizedId === rfidRemovalTargetId.value) {
        const removedItem = removeOneByTagId(normalizedId);
        lastRfidEvent.value = {
          action: 'removed',
          productId: normalizedId,
          item: removedItem
        };
        clearRfidRemovalTarget();
      } else {
        lastRfidEvent.value = {
          action: 'ignored',
          productId: normalizedId,
          reason: 'pending-removal'
        };
      }
      return;
    }

    const added = addProductByLocalId(normalizedId);
    lastRfidEvent.value = {
      action: added ? 'added' : 'not-found',
      productId: normalizedId
    };
  };

  const fetchRecommendation = async () => {
    isLoadingRecommendation.value = true;
    try {
      const productIds = cartItems.value.map(item => item.product_id || item.id);
      const data = await getRecommendation(productIds);
      recommendedProduct.value = data;
    } catch (error) {
      console.error('Recommendation fetch failed:', error);
      recommendedProduct.value = null;
    } finally {
      isLoadingRecommendation.value = false;
    }
  };
  
  const applyCoupon = (coupon) => {
    selectedCoupon.value = coupon;
  };

  const clearCoupon = () => {
    selectedCoupon.value = null;
  };

  const clearCart = () => {
    cartItems.value = [];
    lastAddedProductLocation.value = null;
    try {
      localStorage.removeItem(CART_STORAGE_KEY);
    } catch (error) {
      console.warn('Cart storage clear failed:', error);
    }
  };

  watch(cartItems, () => {
    fetchRecommendation();
  }, { deep: true, immediate: true });

  watch(cartItems, (items) => {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    } catch (error) {
      console.warn('Cart storage save failed:', error);
    }
  }, { deep: true });

  loadCartFromStorage();

  return {
    allProducts,
    cartItems,
    selectedCoupon,
    cartCount,
    cartQuantity,
    totalProductPrice,
    discountAmount,
    finalPrice,
    addProductByLocalId,
    addProduct,
    removeOneByTagId,
    recommendedProduct,
    isLoadingRecommendation,
    fetchRecommendation,
    loadAllProducts,
    handleRfidScan,
    setRfidRemovalTarget,
    clearRfidRemovalTarget,
    lastRfidEvent,
    lastAddedProductLocation,
    getFilteredProducts,
    applyCoupon,
    clearCoupon,
    clearCart
  };
});
