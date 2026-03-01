import { MAP_INFO } from '@/config'

/**
 * 월드 좌표(m)를 캔버스 픽셀 좌표(x)로 변환
 */
export const toCanvasX = (worldX, canvasWidth, imageWidth, zoom, offsetX) => {
  const pixelX = (worldX - MAP_INFO.origin[0]) / MAP_INFO.resolution
  const ratio = canvasWidth / imageWidth
  return (pixelX * ratio * zoom) + (canvasWidth * offsetX)
}

/**
 * 월드 좌표(m)를 캔버스 픽셀 좌표(y)로 변환
 */
export const toCanvasY = (worldY, canvasHeight, imageHeight, zoom, offsetY) => {
  const pixelY = (worldY - MAP_INFO.origin[1]) / MAP_INFO.resolution
  const ratio = canvasHeight / imageHeight
  return (canvasHeight - (pixelY * ratio)) * zoom + (canvasHeight * offsetY)
}

/**
 * 배경 지도 렌더링
 */
export const drawBackground = (ctx, mapImage, canvas, config) => {
  ctx.save()
  const canvasOffsetX = canvas.width * config.offsetX
  const canvasOffsetY = canvas.height * config.offsetY
  ctx.translate(canvasOffsetX, canvasOffsetY)
  ctx.scale(config.zoom, config.zoom)
  ctx.drawImage(mapImage, 0, 0, canvas.width, canvas.height)
  ctx.restore()
}

/**
 * 선 경로 렌더링 (계획 경로 또는 주행 경로)
 */
export const drawPath = (ctx, path, canvas, mapImage, config, style) => {
  if (!path || path.length < 2) return

  ctx.beginPath()
  ctx.strokeStyle = style.color || '#000'
  ctx.lineWidth = style.lineWidth || 2
  if (style.dashed) ctx.setLineDash(style.dashed)
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'

  const start = path[0]
  ctx.moveTo(
    toCanvasX(start.x, canvas.width, mapImage.width, config.zoom, config.offsetX),
    toCanvasY(start.y, canvas.height, mapImage.height, config.zoom, config.offsetY)
  )

  for (let i = 1; i < path.length; i++) {
    const p = path[i]
    ctx.lineTo(
      toCanvasX(p.x, canvas.width, mapImage.width, config.zoom, config.offsetX),
      toCanvasY(p.y, canvas.height, mapImage.height, config.zoom, config.offsetY)
    )
  }
  ctx.stroke()
  ctx.setLineDash([]) // Reset
}

/**
 * 마커(점) 렌더링
 */
export const drawMarker = (ctx, x, y, canvas, mapImage, config, style) => {
  const cx = toCanvasX(x, canvas.width, mapImage.width, config.zoom, config.offsetX)
  const cy = toCanvasY(y, canvas.height, mapImage.height, config.zoom, config.offsetY)

  ctx.beginPath()
  ctx.arc(cx, cy, style.radius || 10, 0, 2 * Math.PI)
  ctx.fillStyle = style.color || '#3B82F6'
  ctx.fill()
  
  if (style.strokeColor) {
    ctx.strokeStyle = style.strokeColor
    ctx.lineWidth = style.strokeWidth || 2
    ctx.stroke()
  }
}
