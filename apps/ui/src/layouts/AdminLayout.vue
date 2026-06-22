<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useAdminAuthStore } from "@/stores/adminAuth";

const { t } = useI18n();
const router = useRouter();
const authStore = useAdminAuthStore();

async function handleLogout(): Promise<void> {
  await authStore.logout();
  router.push({ name: "admin-login" });
}
</script>

<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-grey-9 text-white">
      <q-toolbar>
        <q-toolbar-title>{{ t("app.adminDashboard") }}</q-toolbar-title>
        <q-btn flat :label="t('app.logout')" @click="handleLogout" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>
