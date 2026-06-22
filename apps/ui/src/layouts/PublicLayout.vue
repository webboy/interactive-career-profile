<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { usePublicSettingsStore } from "@/stores/publicSettings";

const { t } = useI18n();
const router = useRouter();
const settingsStore = usePublicSettingsStore();

const languageOptions = computed(() =>
  settingsStore.supportedLanguages.map((value) => ({ label: value.toUpperCase(), value })),
);

function navigate(path: string): void {
  router.push(path);
}
</script>

<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-toolbar-title>{{ settingsStore.appName }}</q-toolbar-title>
        <q-btn flat :label="t('app.privacy')" @click="navigate('/privacy')" />
        <q-btn flat :label="t('app.terms')" @click="navigate('/terms')" />
        <q-select
          v-if="languageOptions.length"
          dense
          outlined
          dark
          :label="t('app.language')"
          :options="languageOptions"
          :model-value="settingsStore.selectedLanguage"
          emit-value
          map-options
          class="q-ml-md"
          style="min-width: 120px"
          @update:model-value="settingsStore.setLanguage"
        />
        <q-btn flat :label="t('app.adminLogin')" to="/admin/login" class="q-ml-sm" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>
