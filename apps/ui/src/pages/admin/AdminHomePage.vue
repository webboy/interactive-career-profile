<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { useAdminAuthStore } from "@/stores/adminAuth";

const { t } = useI18n();
const authStore = useAdminAuthStore();
</script>

<template>
  <q-page padding>
    <h1 class="text-h4">{{ t("app.adminDashboard") }}</h1>
    <p v-if="authStore.user">
      {{ t("admin.welcome", { email: authStore.user.email }) }}
    </p>
  </q-page>
</template>
