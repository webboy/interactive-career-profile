<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import {
  createCareerRecord,
  deleteCareerRecord,
  listCareerRecords,
  updateCareerRecord,
} from "@/api/admin";
import type { CareerRecord, CareerRecordType, EmbeddingStatus, Visibility } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";
import ConfirmDeleteDialog from "@/components/admin/ConfirmDeleteDialog.vue";
import VisibilityBadge from "@/components/admin/VisibilityBadge.vue";

const { t } = useI18n();
const records = ref<CareerRecord[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const dialogOpen = ref(false);
const editing = ref<CareerRecord | null>(null);
const deleteDialog = ref<InstanceType<typeof ConfirmDeleteDialog> | null>(null);
const pendingDelete = ref<CareerRecord | null>(null);

const form = reactive({
  record_type: "experience" as CareerRecordType,
  title: "",
  summary: "",
  content: "",
  visibility: "public" as Visibility,
  source: "",
  tags: "",
  start_date: "",
  end_date: "",
  sort_order: 0,
  embedding_status: "not_required" as EmbeddingStatus,
});

const recordTypeOptions = [
  "experience", "project", "skill", "education", "certification",
  "language", "achievement", "leadership", "availability", "other",
];
const visibilityOptions = ["public", "private", "draft", "archived"];

function resetForm(): void {
  form.record_type = "experience";
  form.title = "";
  form.summary = "";
  form.content = "";
  form.visibility = "public";
  form.source = "";
  form.tags = "";
  form.start_date = "";
  form.end_date = "";
  form.sort_order = 0;
  form.embedding_status = "not_required";
  editing.value = null;
}

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    records.value = await listCareerRecords();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

function openCreate(): void {
  resetForm();
  dialogOpen.value = true;
}

function openEdit(record: CareerRecord): void {
  editing.value = record;
  form.record_type = record.record_type;
  form.title = record.title;
  form.summary = record.summary ?? "";
  form.content = record.content;
  form.visibility = record.visibility;
  form.source = record.source ?? "";
  form.tags = record.tags ?? "";
  form.start_date = record.start_date ?? "";
  form.end_date = record.end_date ?? "";
  form.sort_order = record.sort_order;
  form.embedding_status = record.embedding_status;
  dialogOpen.value = true;
}

async function save(): Promise<void> {
  const payload = {
    record_type: form.record_type,
    title: form.title,
    summary: form.summary || null,
    content: form.content,
    visibility: form.visibility,
    source: form.source || null,
    tags: form.tags || null,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    sort_order: form.sort_order,
    embedding_status: form.embedding_status,
  };
  try {
    if (editing.value) {
      await updateCareerRecord(editing.value.id, payload);
    } else {
      await createCareerRecord(payload);
    }
    dialogOpen.value = false;
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

function confirmDelete(record: CareerRecord): void {
  pendingDelete.value = record;
  deleteDialog.value?.show();
}

async function remove(): Promise<void> {
  if (!pendingDelete.value) return;
  try {
    await deleteCareerRecord(pendingDelete.value.id);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

async function archive(record: CareerRecord): Promise<void> {
  try {
    await updateCareerRecord(record.id, {
      record_type: record.record_type,
      title: record.title,
      summary: record.summary,
      content: record.content,
      visibility: "archived",
      source: record.source,
      tags: record.tags,
      start_date: record.start_date,
      end_date: record.end_date,
      sort_order: record.sort_order,
      embedding_status: record.embedding_status,
      embedding_error: record.embedding_error,
    });
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.careerRecords')" />
    <div class="q-mb-md">
      <q-btn color="primary" :label="t('admin.create')" @click="openCreate" />
    </div>
    <AdminLoadingError :loading="loading" :error="error" />
    <q-table
      v-if="!loading"
      :rows="records"
      :columns="[
        { name: 'title', label: t('admin.title'), field: 'title', align: 'left' },
        { name: 'record_type', label: t('admin.type'), field: 'record_type', align: 'left' },
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
          <q-btn flat dense :label="t('admin.edit')" @click="openEdit(props.row)" />
          <q-btn flat dense :label="t('admin.archive')" @click="archive(props.row)" />
          <q-btn flat dense color="negative" :label="t('admin.delete')" @click="confirmDelete(props.row)" />
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialogOpen">
      <q-card style="min-width: 520px">
        <q-card-section class="text-h6">{{ editing ? t('admin.edit') : t('admin.create') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-select v-model="form.record_type" :options="recordTypeOptions" :label="t('admin.type')" />
          <q-input v-model="form.title" :label="t('admin.title')" />
          <q-input v-model="form.summary" :label="t('admin.summary')" />
          <q-input v-model="form.content" type="textarea" autogrow :label="t('admin.content')" />
          <q-select v-model="form.visibility" :options="visibilityOptions" :label="t('admin.visibility')" />
          <q-input v-model="form.source" :label="t('admin.source')" />
          <q-input v-model="form.tags" :label="t('admin.tags')" />
          <q-input v-model="form.start_date" :label="t('admin.startDate')" />
          <q-input v-model="form.end_date" :label="t('admin.endDate')" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat :label="t('admin.cancel')" v-close-popup />
          <q-btn color="primary" :label="t('admin.save')" @click="save" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <ConfirmDeleteDialog ref="deleteDialog" @confirm="remove" />
  </q-page>
</template>
