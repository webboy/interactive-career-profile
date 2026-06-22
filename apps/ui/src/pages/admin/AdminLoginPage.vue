<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { useAdminAuthStore } from "@/stores/adminAuth";

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const authStore = useAdminAuthStore();

const email = ref("");
const password = ref("");

async function submitLogin(): Promise<void> {
  const ok = await authStore.login(email.value, password.value);
  if (!ok) {
    return;
  }
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/admin";
  router.push(redirect);
}
</script>

<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <q-page padding class="flex flex-center">
        <q-card style="min-width: 360px">
          <q-card-section>
            <div class="text-h6">{{ t("admin.loginTitle") }}</div>
          </q-card-section>
          <q-card-section class="q-gutter-md">
            <q-input v-model="email" :label="t('admin.email')" type="email" />
            <q-input v-model="password" :label="t('admin.password')" type="password" />
            <q-banner v-if="authStore.error" rounded class="bg-red-1 text-negative">
              {{ authStore.error }}
            </q-banner>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn color="primary" :label="t('admin.login')" :loading="authStore.loading" @click="submitLogin" />
          </q-card-actions>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>
