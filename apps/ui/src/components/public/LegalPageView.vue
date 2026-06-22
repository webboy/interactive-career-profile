<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { LegalPageResponse } from "@/api/types";
import { renderLegalMarkdown } from "@/utils/format";

const props = defineProps<{
  fetchPage: () => Promise<LegalPageResponse>;
}>();

const { t } = useI18n();
const page = ref<LegalPageResponse | null>(null);
const error = ref<string | null>(null);
const loading = ref(true);

onMounted(async () => {
  loading.value = true;
  error.value = null;
  try {
    page.value = await props.fetchPage();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("legal.loadError");
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="legal-page">
    <q-banner v-if="loading" rounded class="bg-grey-3">
      {{ t("legal.loading") }}
    </q-banner>
    <q-banner v-else-if="error" rounded class="bg-red-1 text-negative">
      {{ error }}
    </q-banner>
    <div v-else-if="page" class="q-gutter-md">
      <h1 class="text-h4">{{ page.title }}</h1>
      <div class="legal-content" v-html="renderLegalMarkdown(page.content)" />
      <div class="text-caption text-grey">
        {{ t("legal.updatedAt", { date: new Date(page.updated_at).toLocaleString() }) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.legal-content :deep(h1) {
  font-size: 1.5rem;
  margin: 1rem 0 0.5rem;
}
.legal-content :deep(h2) {
  font-size: 1.25rem;
  margin: 0.75rem 0 0.5rem;
}
.legal-content :deep(h3) {
  font-size: 1.1rem;
  margin: 0.5rem 0;
}
</style>
