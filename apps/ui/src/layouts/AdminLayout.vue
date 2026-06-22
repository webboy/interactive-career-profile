<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import AdminNavList from "@/components/admin/AdminNavList.vue";
import { useAdminAuthStore } from "@/stores/adminAuth";

const { t } = useI18n();
const router = useRouter();
const authStore = useAdminAuthStore();
const drawerOpen = ref(true);

async function handleLogout(): Promise<void> {
  await authStore.logout();
  router.push({ name: "admin-login" });
}
</script>

<template>
  <q-layout view="hHh LpR lFf">
    <q-header elevated class="bg-grey-9 text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="drawerOpen = !drawerOpen" />
        <q-toolbar-title>{{ t("app.adminDashboard") }}</q-toolbar-title>
        <q-btn flat :label="t('app.logout')" @click="handleLogout" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawerOpen" show-if-above bordered>
      <AdminNavList />
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>
