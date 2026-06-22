<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { getRetrievalLog, listRetrievalLogs, listUnansweredPrompts } from "@/api/admin";
import type { RetrievalLog, UnansweredPrompt } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";
import SourceTypeBadge from "@/components/admin/SourceTypeBadge.vue";
import VisibilityBadge from "@/components/admin/VisibilityBadge.vue";

const { t } = useI18n();
const logs = ref<RetrievalLog[]>([]);
const prompts = ref<UnansweredPrompt[]>([]);
const selectedLog = ref<RetrievalLog | null>(null);
const loading = ref(true);
const detailLoading = ref(false);
const error = ref<string | null>(null);

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    [logs.value, prompts.value] = await Promise.all([
      listRetrievalLogs(),
      listUnansweredPrompts(),
    ]);
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

async function openLog(id: number): Promise<void> {
  detailLoading.value = true;
  try {
    selectedLog.value = await getRetrievalLog(id);
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    detailLoading.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.retrievalLogs')" />
    <AdminLoadingError :loading="loading" :error="error" />

    <div v-if="!loading" class="row q-col-gutter-md">
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section class="text-subtitle1">{{ t('admin.retrievalLogs') }}</q-card-section>
          <q-list bordered separator>
            <q-item v-for="log in logs" :key="log.id" clickable @click="openLog(log.id)">
              <q-item-section>
                <q-item-label>#{{ log.id }} · {{ log.query }}</q-item-label>
                <q-item-label caption>
                  {{ log.had_usable_context ? t('admin.usableContext') : t('admin.noUsableContext') }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section class="text-subtitle1">{{ t('admin.unansweredPrompts') }}</q-card-section>
          <q-list bordered separator>
            <q-item v-for="prompt in prompts" :key="prompt.id">
              <q-item-section>
                <q-item-label>{{ prompt.query }}</q-item-label>
                <q-item-label caption>{{ prompt.reason }} · log #{{ prompt.retrieval_log_id ?? '-' }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
    </div>

    <q-card v-if="selectedLog" class="q-mt-md">
      <q-card-section class="text-subtitle1">
        {{ t('admin.logDetail', { id: selectedLog.id }) }}
      </q-card-section>
      <q-banner v-if="detailLoading" rounded class="bg-grey-3">{{ t('app.loading') }}</q-banner>
      <q-list v-else bordered separator>
        <q-item v-for="item in selectedLog.items" :key="item.id">
          <q-item-section>
            <q-item-label>
              <SourceTypeBadge :source-type="item.source_type" />
              {{ item.title }}
            </q-item-label>
            <q-item-label caption>{{ item.snippet }}</q-item-label>
            <q-item-label caption>
              {{ item.was_used ? t('admin.used') : t('admin.notUsed') }}
              · score {{ item.score ?? '-' }}
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <VisibilityBadge :visibility="item.visibility" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>
  </q-page>
</template>
