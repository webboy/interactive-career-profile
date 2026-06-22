<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  chunkDocument,
  embedDocumentChunk,
  extractDocument,
  getDocument,
  listDocumentChunks,
  requestDocumentEmbedding,
  retryDocumentIngestion,
  updateDocument,
  updateDocumentChunkVisibility,
} from "@/api/admin";
import type { DocumentChunk, DocumentRecord, Visibility } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";
import VisibilityBadge from "@/components/admin/VisibilityBadge.vue";

const { t } = useI18n();
const route = useRoute();
const documentId = computed(() => Number(route.params.id));

const document = ref<DocumentRecord | null>(null);
const chunks = ref<DocumentChunk[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const actionLoading = ref<string | null>(null);

const editForm = reactive({ title: "", visibility: "draft" as Visibility });
const visibilityOptions = ["public", "private", "draft", "archived"];

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    document.value = await getDocument(documentId.value);
    chunks.value = await listDocumentChunks(documentId.value);
    editForm.title = document.value.title;
    editForm.visibility = document.value.visibility;
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

async function runAction(name: string, action: () => Promise<unknown>): Promise<void> {
  actionLoading.value = name;
  try {
    await action();
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    actionLoading.value = null;
  }
}

async function saveDocument(): Promise<void> {
  await runAction("save", () => updateDocument(documentId.value, editForm));
}

async function updateChunkVisibility(chunk: DocumentChunk, visibility: Visibility): Promise<void> {
  await runAction(`chunk-${chunk.id}`, () => updateDocumentChunkVisibility(chunk.id, visibility));
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="document?.title || t('admin.nav.documents')" />
    <AdminLoadingError :loading="loading" :error="error" />

    <div v-if="document && !loading" class="q-gutter-md">
      <q-card>
        <q-card-section class="row q-col-gutter-md items-center">
          <div class="col">
            <div><strong>{{ t('admin.sourceType') }}:</strong> {{ document.source_type }}</div>
            <div><strong>{{ t('admin.fileType') }}:</strong> {{ document.file_type || '-' }}</div>
            <div><strong>{{ t('admin.status') }}:</strong> {{ document.status }}</div>
            <div><strong>{{ t('admin.embeddingStatus') }}:</strong> {{ document.embedding_status }}</div>
            <VisibilityBadge :visibility="document.visibility" />
          </div>
        </q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model="editForm.title" :label="t('admin.title')" />
          <q-select v-model="editForm.visibility" :options="visibilityOptions" :label="t('admin.visibility')" />
        </q-card-section>
        <q-card-actions>
          <q-btn color="primary" :label="t('admin.save')" :loading="actionLoading === 'save'" @click="saveDocument" />
          <q-btn :label="t('admin.extract')" :loading="actionLoading === 'extract'" @click="runAction('extract', () => extractDocument(documentId))" />
          <q-btn :label="t('admin.chunk')" :loading="actionLoading === 'chunk'" @click="runAction('chunk', () => chunkDocument(documentId))" />
          <q-btn :label="t('admin.retryIngestion')" :loading="actionLoading === 'retry'" @click="runAction('retry', () => retryDocumentIngestion(documentId))" />
          <q-btn :label="t('admin.requestEmbedding')" :loading="actionLoading === 'embed-doc'" @click="runAction('embed-doc', () => requestDocumentEmbedding(documentId))" />
        </q-card-actions>
      </q-card>

      <q-card v-if="document.extracted_text">
        <q-card-section class="text-subtitle1">{{ t('admin.extractedText') }}</q-card-section>
        <q-card-section><pre class="doc-text">{{ document.extracted_text }}</pre></q-card-section>
      </q-card>

      <q-card>
        <q-card-section class="text-subtitle1">{{ t('admin.chunks') }} ({{ chunks.length }})</q-card-section>
        <q-list bordered separator>
          <q-item v-for="chunk in chunks" :key="chunk.id">
            <q-item-section>
              <q-item-label>#{{ chunk.chunk_index }} · {{ chunk.embedding_status }}</q-item-label>
              <q-item-label caption>{{ chunk.content.slice(0, 180) }}...</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-select
                dense
                :model-value="chunk.visibility"
                :options="visibilityOptions"
                style="min-width: 120px"
                @update:model-value="(v) => updateChunkVisibility(chunk, v as Visibility)"
              />
              <q-btn
                flat
                dense
                :label="t('admin.embed')"
                :loading="actionLoading === `chunk-${chunk.id}`"
                @click="runAction(`chunk-${chunk.id}`, () => embedDocumentChunk(chunk.id))"
              />
            </q-item-section>
          </q-item>
        </q-list>
      </q-card>
    </div>
  </q-page>
</template>

<style scoped>
.doc-text {
  white-space: pre-wrap;
  font-family: inherit;
}
</style>
