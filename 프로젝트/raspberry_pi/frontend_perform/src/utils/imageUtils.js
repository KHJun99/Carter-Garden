import { API_URL } from '@/config';

/**
 * 상품 객체를 받아 완전한 이미지 URL을 반환하는 함수
 * @param {Object} product - 상품 객체 (image_url 속성 포함)
 * @returns {string|null} - 완전한 이미지 URL 또는 null
 */
export const getImageUrl = (product) => {
  if (!product || !product.image_url) return null;

  // 이미 http로 시작하는 절대 경로면 그대로 반환
  if (product.image_url.startsWith('http')) return product.image_url;

  // API_URL에서 /api를 제거하여 Base URL 생성
  const baseUrl = (API_URL || '').replace(/\/api\/?$/, '');

  // 이미지 경로에서 static/ 중복 제거 및 슬래시 정리
  let path = product.image_url.replace(/^\/?static\//, '');

  // static/images/ 경로 보장
  return `${baseUrl}/static/images/${path.startsWith('/') ? path.slice(1) : path}`;
};
