import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ProductListView from '../views/ProductListView.vue'
import CartView from '../views/CartView.vue'
import GuideView from '../views/GuideView.vue'
import FinishShopView from '../views/FinishShopView.vue'
import PaymentView from '../views/PaymentView.vue'
import LoginView from '../views/LoginView.vue'
import ThanksView from '../views/ThanksView.vue'
import FollowView from '../views/FollowView.vue'
import RegisterYoloView from '../views/RegisterYoloView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/register-yolo',
      name: 'register-yolo',
      component: RegisterYoloView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/products',
      name: 'products',
      component: ProductListView
    },
    {
      path: '/cart',
      name: 'cart',
      component: CartView
    },
    {
      path: '/guide',
      name: 'guide',
      component: GuideView
    },
    {
      path: '/finish',
      name: 'finish',
      component: FinishShopView
    },
    {
      path: '/payment',
      name: 'payment',
      component: PaymentView
    },
    {
      path: '/thanks',
      name: 'thanks',
      component: ThanksView
    },
    {
      path: '/follow',
      name: 'follow',
      component: FollowView
    }
  ]
})

export default router
