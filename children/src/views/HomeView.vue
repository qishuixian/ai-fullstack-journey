<script setup lang="ts">
import { ElButton } from "element-plus";
import "element-plus/es/components/button/style/css";
</script>

<template>
  <section class="welcome" aria-labelledby="welcome-title">
    <div class="sun" aria-hidden="true">☀</div>
    <p class="eyebrow">你好，小小探索家！</p>
    <h1 id="welcome-title">让语言的种子，<br /><span>慢慢发芽。</span></h1>
    <p class="intro">选一个喜欢的语言，开启今天的奇妙旅程吧。</p>
    <div class="language-grid">
      <article class="language-card chinese">
        <div class="letter" aria-hidden="true">中<span>✦</span></div>
        <p class="card-label">CHINESE</p>
        <h2>中文乐园</h2>
        <p>一字一句，发现中文的美好</p>
        <ElButton class="entry-button" @click="$router.push('/zhonwen')">进入中文 <span aria-hidden="true">↗</span></ElButton>
      </article>
      <article class="language-card english">
        <div class="letter" aria-hidden="true">Aa<span>✧</span></div>
        <p class="card-label">ENGLISH</p>
        <h2>英文乐园</h2>
        <p>ABC，和新世界说声 Hello</p>
        <ElButton class="entry-button" @click="$router.push('/yingwen')">进入英文 <span aria-hidden="true">↗</span></ElButton>
      </article>
    </div>
    <p class="welcome-note">小小的好奇心，大大的世界。</p>
  </section>
</template>
