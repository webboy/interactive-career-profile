<script setup lang="ts">
import { useI18n } from "vue-i18n";
import AdminNavList from "@/components/admin/AdminNavList.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";

const { t } = useI18n();
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('app.adminDashboard')" :subtitle="t('admin.dashboardIntro')" />
    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section class="text-subtitle1">{{ t("admin.sections.knowledge") }}</q-card-section>
          <AdminNavList />
        </q-card>
      </div>
    </div>
  </q-page>
</template>
