import { ref } from 'vue';
import { API_URL, TOSS_CLIENT_KEY } from '@/config';

export function useTossPayment() {
  const isLoading = ref(false);
  const paymentWidget = ref(null);
  const paymentMethodsWidget = ref(null);

  // 1. Toss Payment SDK 로드 (일반 결제용 - 신용카드)
  const loadTossSdk = () => {
    return new Promise((resolve, reject) => {
      if (window.TossPayments) {
        resolve(window.TossPayments);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://js.tosspayments.com/v1/payment';
      script.onload = () => resolve(window.TossPayments);
      script.onerror = () => reject(new Error('Toss SDK 로드 실패'));
      document.head.appendChild(script);
    });
  };

  // 2. Toss Payment Widget SDK 로드 (간편결제용 - 모달)
  const loadWidgetSdk = () => {
    return new Promise((resolve, reject) => {
      if (window.PaymentWidget) {
        resolve(window.PaymentWidget);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://js.tosspayments.com/v1/payment-widget';
      script.onload = () => {
        if (window.PaymentWidget) {
          resolve(window.PaymentWidget);
        } else {
          reject(new Error('Payment Widget SDK 로드 실패'));
        }
      };
      script.onerror = () => reject(new Error('Payment Widget SDK 스크립트 로드 실패'));
      document.head.appendChild(script);
    });
  };

  // 3. 일반 결제 요청 (신용카드)
  const requestTossPayment = async ({
    paymentMethod,
    mobilePayMethod,
    amount,
    orderName
  }) => {
    isLoading.value = true;

    try {
      const tossPayments = await loadTossSdk();
      const toss = tossPayments(TOSS_CLIENT_KEY);

      const orderId = 'ORD-' + Date.now();

      // 현재 프론트엔드 도메인 확인
      const currentOrigin = window.location.origin;
      const nextUrlParam = `next_url=${encodeURIComponent(currentOrigin)}`;

      // 결제 옵션 설정
      const options = {
        amount,
        orderId,
        orderName,
        successUrl: `${API_URL}/payment/toss/success?${nextUrlParam}`,
        failUrl: `${API_URL}/payment/toss/fail?${nextUrlParam}`,
      };

      let method = '카드';

      // Toss 결제창 호출
      await toss.requestPayment(method, options);

    } catch (error) {
      console.error('Toss Payment Error:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  // 4. 위젯 초기화 (간편결제용)
  const initWidget = async (selector, amount) => {
    try {
      isLoading.value = true;

      const PaymentWidgetConstructor = await loadWidgetSdk();

      // 위젯 인스턴스 생성 (한 번만)
      if (!paymentWidget.value) {
        paymentWidget.value = PaymentWidgetConstructor(TOSS_CLIENT_KEY, 'ANONYMOUS');
      }

      // 결제 수단 UI 렌더링
      paymentMethodsWidget.value = paymentWidget.value.renderPaymentMethods(
        selector,
        { value: amount },
        { variantKey: 'DEFAULT' }
      );

      // 렌더링 완료 대기
      await new Promise(resolve => setTimeout(resolve, 800));

      console.log('위젯 렌더링 완료');

      return paymentWidget.value;
    } catch (error) {
      console.error('위젯 초기화 에러:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  // 5. 위젯으로 결제 요청 (간편결제)
  const requestWidgetPayment = async ({ orderName, amount }) => {
    if (!paymentWidget.value) {
      throw new Error('위젯이 초기화되지 않았습니다.');
    }

    try {
      isLoading.value = true;

      const orderId = 'ORD-' + Date.now();
      const currentOrigin = window.location.origin;
      const nextUrlParam = `next_url=${encodeURIComponent(currentOrigin)}`;

      console.log('위젯 결제 요청:', { orderId, orderName, amount });

      // 위젯을 통한 결제 요청
      await paymentWidget.value.requestPayment({
        orderId,
        orderName,
        successUrl: `${API_URL}/payment/toss/success?${nextUrlParam}`,
        failUrl: `${API_URL}/payment/toss/fail?${nextUrlParam}`,
      });

      console.log('결제 요청 완료');

    } catch (error) {
      console.error('결제 요청 에러:', error);

      if (error.code === 'USER_CANCEL') {
        throw new Error('사용자가 결제를 취소했습니다.');
      } else if (error.message) {
        throw error;
      } else {
        throw new Error('결제 요청 중 오류가 발생했습니다.');
      }
    } finally {
      isLoading.value = false;
    }
  };

  // 6. 금액 업데이트
  const updateAmount = (amount) => {
    if (paymentMethodsWidget.value) {
      try {
        paymentMethodsWidget.value.updateAmount({ value: amount });
      } catch (error) {
        console.error('금액 업데이트 에러:', error);
      }
    }
  };

  return {
    isLoading,
    requestTossPayment,      // 신용카드 결제
    initWidget,              // 간편결제 위젯 초기화
    requestWidgetPayment,    // 간편결제 요청
    updateAmount,            // 금액 업데이트
  };
}