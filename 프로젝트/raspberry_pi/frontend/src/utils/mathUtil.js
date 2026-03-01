// 유클리드 거리 계산
export const calcDistance = (x1, y1, x2, y2) => {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
};

// Nav2 호환 쿼터니언 방향 계산
export const calcOrientation = (x1, y1, x2, y2) => {
  const theta = Math.atan2(y2 - y1, x2 - x1);

  return {
    z: Math.sin(theta / 2),
    w: Math.cos(theta / 2)
  };
};
