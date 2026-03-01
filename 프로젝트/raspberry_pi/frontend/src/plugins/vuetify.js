// frontend/src/plugins/vuetify.js

// Vuetify 스타일 및 아이콘 불러오기
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css' 

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Vuetify 인스턴스 생성
export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
  },
})