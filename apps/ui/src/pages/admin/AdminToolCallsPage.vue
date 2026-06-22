<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { listToolCalls } from "@/api/admin";
import type { ToolCallRecord } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";

const { t } = useI18n();
const toolCalls = ref<ToolCallRecord[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    const response = await listToolCalls();
    toolCalls.value = response.tool_calls;
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.toolCalls')" />
    <AdminLoadingError :loading="loading" :error="error" />
    <q-table
      v-if="!loading"
      :rows="toolCalls"
      :columns="[
        { name: 'tool_name', label: t('admin.toolName'), field: 'tool_name', align: 'left' },
        { name: 'status', label: t('admin.status'), field: 'status', align: 'left' },
        { name: 'conversation_id', label: t('admin.conversationId'), field: 'conversation_id', align: 'left' },
        { name: 'error_message', label: t('admin.error'), field: 'error_message', align: 'left' },
      ]"
      row-key="id"
      flat
      bordered
    />
  </q-page>
</template>
