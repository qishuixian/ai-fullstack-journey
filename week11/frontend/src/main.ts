import { createApp } from "vue";
import { ElButton, ElDialog } from "element-plus";
import "element-plus/es/components/button/style/css";
import "element-plus/es/components/dialog/style/css";
import "element-plus/es/components/message/style/css";
import App from "./App.vue";
import "./style.css";
createApp(App).use(ElButton).use(ElDialog).mount("#app");
