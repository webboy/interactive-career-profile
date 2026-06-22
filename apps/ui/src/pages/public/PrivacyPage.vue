<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getPrivacyPage } from "@/api/public";
import type { LegalPageResponse } from "@/api/types";

const page = ref<LegalPageResponse | null>(null);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    page.value = await getPrivacyPage();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load privacy page";
  }
});
</script>

<template>
  <q-page padding>
    <q-banner v-if="error" rounded class="bg-red-1 text-negative">{{ error }}</q-banner>
    <div v-else-if="page" class="q-gutter-md">
      <h1 class="text-h4">{{ page.title }}</h1>
      <pre class="legal-content">{{ page.content }}</pre>
    </div>
  </q-page>
</template>

<style scoped>
.legal-content {
  white-space: pre-wrap;
  font-family: inherit;
}
</style>
