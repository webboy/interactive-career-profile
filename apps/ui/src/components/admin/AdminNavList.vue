<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";

const { t } = useI18n();
const router = useRouter();

const navItems = [
  { labelKey: "admin.nav.dashboard", route: "admin-home" },
  { labelKey: "admin.nav.settings", route: "admin-settings" },
  { labelKey: "admin.nav.legal", route: "admin-legal" },
  { labelKey: "admin.nav.profileItems", route: "admin-profile-items" },
  { labelKey: "admin.nav.careerRecords", route: "admin-career-records" },
  { labelKey: "admin.nav.documents", route: "admin-documents" },
  { labelKey: "admin.nav.conversations", route: "admin-conversations" },
  { labelKey: "admin.nav.retrievalLogs", route: "admin-retrieval-logs" },
  { labelKey: "admin.nav.leads", route: "admin-leads" },
  { labelKey: "admin.nav.toolCalls", route: "admin-tool-calls" },
];

function navigate(name: string): void {
  router.push({ name });
}
</script>

<template>
  <q-list padding>
    <q-item
      v-for="item in navItems"
      :key="item.route"
      clickable
      v-ripple
      @click="navigate(item.route)"
    >
      <q-item-section>{{ t(item.labelKey) }}</q-item-section>
    </q-item>
  </q-list>
</template>
