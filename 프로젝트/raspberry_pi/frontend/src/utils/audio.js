const normalizeBaseUrl = (baseUrl) => {
  if (!baseUrl) return '/'
  return baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`
}

const buildAudioUrl = (relativePath) => {
  const baseUrl = normalizeBaseUrl(import.meta.env.BASE_URL)
  const cleaned = String(relativePath || '').replace(/^\/+/, '')
  return `${baseUrl}${cleaned}`
}

const audioCache = new Map()

export const playSound = (relativePath) => {
  const src = buildAudioUrl(relativePath)
  let audio = audioCache.get(src)

  if (!audio) {
    audio = new Audio(src)
    audio.preload = 'auto'
    audioCache.set(src, audio)
  }

  try {
    audio.currentTime = 0
    const result = audio.play()
    if (result && typeof result.catch === 'function') {
      result.catch(() => {})
    }
  } catch (error) {
    console.warn('Failed to play sound:', error)
  }
}
