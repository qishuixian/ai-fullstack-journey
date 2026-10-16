<script setup lang="ts">
import { useRoute } from "vue-router";
const route = useRoute();
</script>

<template>
  <div :class="['page-shell', { 'study-shell': route.name === 'chinese' }]">
    <header v-if="route.name !== 'chinese'" class="brand"><span aria-hidden="true">✿</span> 语言小乐园 <small>LITTLE LANGUAGE GARDEN</small></header>
    <main><RouterView /></main>
    <footer v-if="route.name !== 'chinese'">每一天，发现一点新世界 <span aria-hidden="true">✦</span></footer>
  </div>
</template>
