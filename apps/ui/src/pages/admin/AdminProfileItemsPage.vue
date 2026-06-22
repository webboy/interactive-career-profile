<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import {
  createProfileItem,
  deleteProfileItem,
  listProfileItems,
  updateProfileItem,
} from "@/api/admin";
import type { ProfileItem, ProfileItemType, Visibility } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";
import ConfirmDeleteDialog from "@/components/admin/ConfirmDeleteDialog.vue";
import VisibilityBadge from "@/components/admin/VisibilityBadge.vue";

const { t } = useI18n();
const items = ref<ProfileItem[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const dialogOpen = ref(false);
const editing = ref<ProfileItem | null>(null);
const deleteDialog = ref<InstanceType<typeof ConfirmDeleteDialog> | null>(null);
const pendingDelete = ref<ProfileItem | null>(null);

const form = reactive({
  key: "",
  type: "text" as ProfileItemType,
  label: "",
  value: "",
  visibility: "private" as Visibility,
  source: "",
  sort_order: 0,
});

const typeOptions = ["text", "link", "email", "location", "language", "availability", "other"];
const visibilityOptions = ["public", "private", "draft", "archived"];

function resetForm(): void {
  form.key = "";
  form.type = "text";
  form.label = "";
  form.value = "";
  form.visibility = "private";
  form.source = "";
  form.sort_order = 0;
  editing.value = null;
}

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    items.value = await listProfileItems();
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

function openEdit(item: ProfileItem): void {
  editing.value = item;
  form.key = item.key;
  form.type = item.type;
  form.label = item.label;
  form.value = item.value;
  form.visibility = item.visibility;
  form.source = item.source ?? "";
  form.sort_order = item.sort_order;
  dialogOpen.value = true;
}

async function save(): Promise<void> {
  try {
    if (editing.value) {
      await updateProfileItem(editing.value.id, {
        ...form,
        source: form.source || null,
      });
    } else {
      await createProfileItem({
        ...form,
        source: form.source || null,
      });
    }
    dialogOpen.value = false;
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

function confirmDelete(item: ProfileItem): void {
  pendingDelete.value = item;
  deleteDialog.value?.show();
}

async function remove(): Promise<void> {
  if (!pendingDelete.value) return;
  try {
    await deleteProfileItem(pendingDelete.value.id);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.profileItems')" />
    <div class="q-mb-md">
      <q-btn color="primary" :label="t('admin.create')" @click="openCreate" />
    </div>
    <AdminLoadingError :loading="loading" :error="error" />
    <q-table
      v-if="!loading"
      :rows="items"
      :columns="[
        { name: 'label', label: t('admin.label'), field: 'label', align: 'left' },
        { name: 'key', label: t('admin.key'), field: 'key', align: 'left' },
        { name: 'type', label: t('admin.type'), field: 'type', align: 'left' },
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
          <q-btn flat dense color="negative" :label="t('admin.delete')" @click="confirmDelete(props.row)" />
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialogOpen">
      <q-card style="min-width: 480px">
        <q-card-section class="text-h6">
          {{ editing ? t('admin.edit') : t('admin.create') }}
        </q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model="form.key" :label="t('admin.key')" />
          <q-input v-model="form.label" :label="t('admin.label')" />
          <q-select v-model="form.type" :options="typeOptions" :label="t('admin.type')" />
          <q-input v-model="form.value" type="textarea" autogrow :label="t('admin.value')" />
          <q-select v-model="form.visibility" :options="visibilityOptions" :label="t('admin.visibility')" />
          <q-input v-model="form.source" :label="t('admin.source')" />
          <q-input v-model.number="form.sort_order" type="number" :label="t('admin.sortOrder')" />
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
