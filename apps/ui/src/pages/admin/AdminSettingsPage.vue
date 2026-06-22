<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { listAdminSettings, updateAdminSetting } from "@/api/admin";
import type { AdminSetting } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";

const { t } = useI18n();
const settings = ref<AdminSetting[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const savingKey = ref<string | null>(null);
const draftValues = ref<Record<string, string>>({});

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    settings.value = await listAdminSettings();
    draftValues.value = Object.fromEntries(settings.value.map((s) => [s.key, s.value]));
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

async function save(setting: AdminSetting): Promise<void> {
  savingKey.value = setting.key;
  try {
    const updated = await updateAdminSetting(
      setting.key,
      draftValues.value[setting.key] ?? "",
      setting.is_secret,
    );
    const index = settings.value.findIndex((s) => s.key === setting.key);
    if (index >= 0) settings.value[index] = updated;
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    savingKey.value = null;
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.settings')" />
    <AdminLoadingError :loading="loading" :error="error" />
    <q-list v-if="!loading && !error" bordered separator>
      <q-item v-for="setting in settings" :key="setting.key">
        <q-item-section>
          <q-item-label>{{ setting.key }}</q-item-label>
          <q-input
            v-model="draftValues[setting.key]"
            dense
            :type="setting.is_secret ? 'password' : 'text'"
          />
        </q-item-section>
        <q-item-section side>
          <q-btn
            color="primary"
            :label="t('admin.save')"
            :loading="savingKey === setting.key"
            @click="save(setting)"
          />
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>
