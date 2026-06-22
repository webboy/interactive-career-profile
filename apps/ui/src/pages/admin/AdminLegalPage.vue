<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import { getAdminLegalPage, updateAdminLegalPage } from "@/api/admin";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";

const { t } = useI18n();
const loading = ref(true);
const error = ref<string | null>(null);
const saving = ref<string | null>(null);

const privacy = reactive({ title: "", content: "" });
const terms = reactive({ title: "", content: "" });

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    const [privacyPage, termsPage] = await Promise.all([
      getAdminLegalPage("privacy"),
      getAdminLegalPage("terms"),
    ]);
    privacy.title = privacyPage.title;
    privacy.content = privacyPage.content;
    terms.title = termsPage.title;
    terms.content = termsPage.content;
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

async function save(slug: "privacy" | "terms"): Promise<void> {
  saving.value = slug;
  try {
    const form = slug === "privacy" ? privacy : terms;
    await updateAdminLegalPage(slug, form.title, form.content);
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    saving.value = null;
  }
}

onMounted(() => void load());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.legal')" />
    <AdminLoadingError :loading="loading" :error="error" />
    <div v-if="!loading && !error" class="q-gutter-lg">
      <q-card v-for="section in [{ slug: 'privacy', form: privacy }, { slug: 'terms', form: terms }]" :key="section.slug">
        <q-card-section class="text-h6">{{ section.slug === 'privacy' ? t('app.privacy') : t('app.terms') }}</q-card-section>
        <q-card-section class="q-gutter-md">
          <q-input v-model="section.form.title" :label="t('admin.title')" />
          <q-input v-model="section.form.content" type="textarea" autogrow :label="t('admin.content')" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn
            color="primary"
            :label="t('admin.save')"
            :loading="saving === section.slug"
            @click="save(section.slug as 'privacy' | 'terms')"
          />
        </q-card-actions>
      </q-card>
    </div>
  </q-page>
</template>
