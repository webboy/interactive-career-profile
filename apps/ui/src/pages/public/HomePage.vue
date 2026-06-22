<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { usePublicSettingsStore } from "@/stores/publicSettings";

const { t } = useI18n();
const settingsStore = usePublicSettingsStore();
</script>

<template>
  <q-page padding>
    <div class="q-gutter-md">
      <h1 class="text-h4">{{ settingsStore.appName }}</h1>
      <p>{{ t("app.homeIntro") }}</p>
      <q-banner v-if="settingsStore.loading" rounded class="bg-grey-3">
        {{ t("app.loading") }}
      </q-banner>
      <q-banner v-else-if="settingsStore.error" rounded class="bg-red-1 text-negative">
        {{ settingsStore.error }}
      </q-banner>
    </div>
  </q-page>
</template>
