import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 引入highlight.js
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css' // 选择一个样式
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 全局注册highlight.js
app.directive('highlight', {
  mounted(el) {
    const blocks = el.querySelectorAll('pre code')
    blocks.forEach(block => {
      hljs.highlightBlock(block)
    })
  }
})

app.mount('#app')