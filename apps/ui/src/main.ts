import { createApp } from "vue";
import { createPinia } from "pinia";
import { Quasar, Notify } from "quasar";
import "@quasar/extras/material-icons/material-icons.css";
import "quasar/dist/quasar.css";
import App from "./App.vue";
import router from "./router";
import { i18n } from "./i18n";
import { usePublicSettingsStore } from "./stores/publicSettings";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(i18n);
app.use(Quasar, {
  plugins: { Notify },
});

const settingsStore = usePublicSettingsStore(pinia);
void settingsStore.loadSettings();

app.mount("#app");
