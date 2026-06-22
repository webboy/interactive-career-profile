<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import {
  createTextDocument,
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "@/api/admin";
import type { DocumentRecord, Visibility } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";
import ConfirmDeleteDialog from "@/components/admin/ConfirmDeleteDialog.vue";
import VisibilityBadge from "@/components/admin/VisibilityBadge.vue";

const { t } = useI18n();
const router = useRouter();
const documents = ref<DocumentRecord[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const uploadOpen = ref(false);
const textOpen = ref(false);
const deleteDialog = ref<InstanceType<typeof ConfirmDeleteDialog> | null>(null);
const pendingDelete = ref<DocumentRecord | null>(null);
const selectedFile = ref<File | null>(null);

const uploadForm = reactive({ title: "", visibility: "draft" as Visibility });
const textForm = reactive({ title: "", content: "", visibility: "draft" as Visibility });
const visibilityOptions = ["public", "private", "draft", "archived"];

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    documents.value = await listDocuments();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

function openDetail(id: number): void {
  router.push({ name: "admin-document-detail", params: { id } });
}

async function submitUpload(): Promise<void> {
  if (!selectedFile.value) return;
  try {
    await uploadDocument(selectedFile.value, uploadForm.title || undefined, uploadForm.visibility);
    uploadOpen.value = false;
    selectedFile.value = null;
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

async function submitText(): Promise<void> {
  try {
    await createTextDocument(textForm);
    textOpen.value = false;
    textForm.title = "";
    textForm.content = "";
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

function confirmDelete(doc: DocumentRecord): void {
  pendingDelete.value = doc;
  deleteDialog.value?.show();
}

async function remove(): Promise<void> {
  if (!pendingDelete.value) return;
  try {
    await deleteDocument(pendingDelete.value.id);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.documents')" />
    <div class="q-mb-md q-gutter-sm">
      <q-btn color="primary" :label="t('admin.uploadDocument')" @click="uploadOpen = true" />
      <q-btn outline color="primary" :label="t('admin.createTextDocument')" @click="textOpen = true" />
    </div>
    <AdminLoadingError :loading="loading" :error="error" />
    <q-table
      v-if="!loading"
      :rows="documents"
      :columns="[
        { name: 'title', label: t('admin.title'), field: 'title', align: 'left' },
        { name: 'source_type', label: t('admin.sourceType'), field: 'source_type', align: 'left' },
        { name: 'file_type', label: t('admin.fileType'), field: 'file_type', align: 'left' },
        { name: 'status', label: t('admin.status'), field: 'status', align: 'left' },
        { name: 'visibility', label: t('admin.visibility'), field: 'visibility', align: 'left' },
        { name: 'actions', label: '', field: 'id', align: 'right' },
      ]"
      row-key="id"
      flat
      bordered
    >
      <template #body-cell-visibility="props">
        <q-td :props="props"><VisibilityBadge :visibility="props.row.visibility" /></q-td>
      </template>
      <template #body-cell-actions="props">
        <q-td :props="props">
          <q-btn flat dense :label="t('admin.view')" @click="openDetail(props.row.id)" />
          <q-btn flat dense color="negative" :label="t('admin.delete')" @click="confirmDelete(props.row)" />
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="uploadOpen">
      <q-card style="min-width: 420px">
        <q-card-section class="text-h6">{{ t('admin.uploadDocument') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-file v-model="selectedFile" :label="t('admin.file')" />
          <q-input v-model="uploadForm.title" :label="t('admin.title')" />
          <q-select v-model="uploadForm.visibility" :options="visibilityOptions" :label="t('admin.visibility')" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat :label="t('admin.cancel')" v-close-popup />
          <q-btn color="primary" :label="t('admin.upload')" @click="submitUpload" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="textOpen">
      <q-card style="min-width: 520px">
        <q-card-section class="text-h6">{{ t('admin.createTextDocument') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model="textForm.title" :label="t('admin.title')" />
          <q-input v-model="textForm.content" type="textarea" autogrow :label="t('admin.content')" />
          <q-select v-model="textForm.visibility" :options="visibilityOptions" :label="t('admin.visibility')" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat :label="t('admin.cancel')" v-close-popup />
          <q-btn color="primary" :label="t('admin.save')" @click="submitText" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <ConfirmDeleteDialog ref="deleteDialog" @confirm="remove" />
  </q-page>
</template>
