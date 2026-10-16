<script setup lang="ts">
defineProps<{ language: "zh" | "en" }>();
</script>

<template>
  <section :class="['language-page', language === 'zh' ? 'chinese' : 'english']">
    <RouterLink class="back-link" to="/">← {{ language === 'zh' ? '返回首页' : 'Back to home' }}</RouterLink>
    <div class="letter" aria-hidden="true">{{ language === 'zh' ? '中' : 'Aa' }}</div>
    <p class="eyebrow">{{ language === 'zh' ? '你好，小小探索家！' : 'HELLO, LITTLE EXPLORER!' }}</p>
    <h1>{{ language === 'zh' ? '欢迎来到中文乐园' : 'Welcome to English Garden' }}</h1>
    <p class="intro">{{ language === 'zh' ? '一字一句，发现中文的美好。' : 'A little curiosity. A whole new world.' }}</p>
    <RouterLink class="switch-link" :to="language === 'zh' ? '/yingwen' : '/zhonwen'">{{ language === 'zh' ? '切换到英文 →' : '进入中文 →' }}</RouterLink>
  </section>
</template>
