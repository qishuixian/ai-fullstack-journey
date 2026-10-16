<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ElButton, ElImage, ElOption, ElSelect } from "element-plus";
import "element-plus/es/components/button/style/css";

import "element-plus/es/components/image/style/css";
import "element-plus/es/components/select/style/css";
import "element-plus/es/components/option/style/css";

const pages = [
  ["上", "园", "早", "水"],
  ["老", "桌", "杯", "玩"],
  ["班", "问", "声", "师"],
  ["幼", "家", "她", "夸"],
  ["虎", "子", "猴", "颈"],
  ["莓", "柿", "蕉", "西"],
  ["卜", "竹", "茄", "洋"],
  ["闪", "电", "沙", "冰"],
  ["鼻", "闻", "说", "朵"],
  ["袖", "扣", "裤", "鞋"],
  ["刷", "牙", "中", "白"],
  ["我", "不", "按", "时"],
  ["成", "棉", "哥", "姐"],
  ["雪", "堆", "对", "雪"],
  ["灯", "笼", "炮", "饺"],
  ["新", "衣", "帽", "哈"],
];
const images = import.meta.glob<string>("../images/*.png", {
  eager: true,
  query: "?url",
  import: "default",
});
const showImage = ref(false);
const page = ref(1);
const characterIndex = ref(0);
const characters = computed(() => pages[page.value - 1]);
const character = computed(() => characters.value[characterIndex.value]);
watch(page, () => {
  characterIndex.value = 0;
  showImage.value = false;
});
function changeCharacter(offset: number) {
  showImage.value = false;
  characterIndex.value = Math.min(characters.value.length - 1, Math.max(0, characterIndex.value + offset));
}
</script>

<template>
  <section class="chinese-study" aria-label="中文识字卡片">
    <header class="study-toolbar">
      <RouterLink to="/" class="study-home">← 返回首页</RouterLink>
    <nav class="study-pagination" aria-label="切换当前页的字">
      <ElButton :disabled="characterIndex === 0" @click="changeCharacter(-1)">← 上一个字</ElButton>
      <span class="page-counter">{{ characterIndex + 1 }} / {{ characters.length }}</span>
      <ElButton :disabled="characterIndex === characters.length - 1" @click="changeCharacter(1)">下一个字 →</ElButton>
    </nav>
      <ElSelect v-model="page" class="page-select" aria-label="选择页码" :teleported="true">
        <ElOption v-for="(_, index) in pages" :key="index" :label="`第${index + 1}页`" :value="index + 1" />
      </ElSelect>
    </header>

<div class="character-grid" aria-live="polite" :aria-label="`第${page}页`">
      <button :key="`${page}-${characterIndex}`" type="button" class="character-card" :aria-label="`${character}，点击显示${showImage ? '字' : '图片'}`" :aria-pressed="!!showImage" @click="showImage = !showImage">
        <span v-if="!showImage" class="character-text">{{ character }}</span>
        <ElImage v-else class="character-image" :src="images[`../images/${character}.png`]" :alt="character" fit="contain">
          <template #placeholder><span class="image-status">图片加载中…</span></template>
          <template #error><span class="image-status">{{ character }} · 图片加载失败，点击显示字</span></template>
        </ElImage>
      </button>
    </div>


  </section>
</template>

<style scoped>
.chinese-study {
  display: flex; flex-direction: column; flex: 1; min-height: 0; gap: 20px;
  --el-color-primary: #a64b2f;
  --el-color-primary-light-3: #bd745d;
  --el-color-primary-dark-2: #853c26;
  --el-color-primary-light-9: #fff0df;
  --el-border-radius-base: 12px;
}
.study-toolbar { flex-shrink: 0; display: flex; align-items: center; justify-content: flex-end; gap: 16px; }
.page-select { width: 150px; flex-shrink: 0; }
.page-select :deep(.el-select__wrapper) { min-height: 46px; font-size: 16px; }
.study-home { display: inline-flex; align-items: center; min-height: 44px; text-decoration: none; color: #80523b; white-space: nowrap; font-size: 14px; flex-shrink: 0; }
.character-grid { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr); gap: 20px; }
.character-card { padding: 0; cursor: pointer; font: inherit; -webkit-appearance: none; appearance: none; display: flex; align-items: center; justify-content: center; min-width: 0; height: 100%; min-height: 0; width: 100%; background: #fff; border: 1px solid #eadfce; border-radius: 22px; overflow: hidden; box-shadow: 0 5px 20px #454c3208; }
.character-text { font-family: "KaiTi", "STKaiti", "Kaiti SC", "Noto Serif CJK SC", serif; font-size: min(56vw, 72vh, 680px); font-size: min(56vw, 72dvh, 680px); line-height: 1; color: #303e35; }
.character-image { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.character-image :deep(.el-image__inner) { width: 100%; height: 100%; object-position: center; }
.image-status { display: flex; height: 100%; align-items: center; justify-content: center; padding: 16px; text-align: center; color: #697367; font-size: 14px; }
.study-pagination { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex: 1; min-width: 0; }
.study-pagination .el-button { height: 46px; min-width: 112px; margin: 0; font-size: 15px; }
.page-counter { font-size: 14px; color: #697367; white-space: nowrap; }
@media (max-width: 600px) {
  .chinese-study { gap: 12px; }
  .study-home { font-size: 11px; }
  .study-toolbar { gap: 4px; }
  .page-select { width: 76px; }
  .character-grid { gap: 12px; }
  .character-card {  border-radius: 16px; }
  .character-text { font-size: min(82vw, 68vh, 440px); font-size: min(82vw, 68dvh, 440px); }
  .study-pagination { gap: 4px; }
  .study-pagination .el-button { min-width: 0; padding: 8px 4px; font-size: 11px; }
  .page-counter { font-size: 12px; }
  .page-select :deep(.el-select__wrapper) { padding: 8px; font-size: 13px; }
}
@media (max-width: 350px) {
  .page-select { width: 70px; }
  .study-toolbar, .study-pagination { gap: 4px; }
  .study-pagination .el-button { padding: 8px 3px; font-size: 11px; }
}
</style>
