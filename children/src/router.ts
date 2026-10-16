import { createRouter, createWebHistory } from "vue-router";
import HomeView from "./views/HomeView.vue";
import LanguageView from "./views/LanguageView.vue";
import ChineseView from "./views/ChineseView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", component: HomeView, meta: { title: "语言小乐园" } },
    { path: "/zhonwen", name: "chinese", component: ChineseView, meta: { title: "中文乐园" } },
    { path: "/yingwen", component: LanguageView, props: { language: "en" }, meta: { title: "English Garden", lang: "en" } },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior: () => ({ top: 0 }),
});

router.afterEach((to) => {
  document.title = String(to.meta.title);
  document.documentElement.lang = to.meta.lang === "en" ? "en" : "zh-CN";
});

export default router;
