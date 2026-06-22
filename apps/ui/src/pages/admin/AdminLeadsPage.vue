<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { listFollowUpRequests, listJobSubmissions, listMeetingRequests } from "@/api/admin";
import type { FollowUpRequest, JobSubmission, MeetingRequest } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";

const { t } = useI18n();
const tab = ref("meetings");
const meetings = ref<MeetingRequest[]>([]);
const followUps = ref<FollowUpRequest[]>([]);
const jobs = ref<JobSubmission[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

async function load(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    [meetings.value, followUps.value, jobs.value] = await Promise.all([
      listMeetingRequests(),
      listFollowUpRequests(),
      listJobSubmissions(),
    ]);
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
    <AdminPageHeader :title="t('admin.nav.leads')" />
    <AdminLoadingError :loading="loading" :error="error" />

    <q-tabs v-if="!loading" v-model="tab" class="q-mb-md">
      <q-tab name="meetings" :label="t('admin.leads.meetings')" />
      <q-tab name="followups" :label="t('admin.leads.followUps')" />
      <q-tab name="jobs" :label="t('admin.leads.jobs')" />
    </q-tabs>

    <q-tab-panels v-if="!loading" v-model="tab" animated>
      <q-tab-panel name="meetings">
        <q-list bordered separator>
          <q-item v-for="item in meetings" :key="item.id">
            <q-item-section>
              <q-item-label>{{ item.requester_name }} · {{ item.requester_email }}</q-item-label>
              <q-item-label caption>{{ item.message }}</q-item-label>
              <q-item-label caption>{{ item.preferred_times }}</q-item-label>
            </q-item-section>
            <q-item-section side>{{ item.status }}</q-item-section>
          </q-item>
        </q-list>
      </q-tab-panel>
      <q-tab-panel name="followups">
        <q-list bordered separator>
          <q-item v-for="item in followUps" :key="item.id">
            <q-item-section>
              <q-item-label>{{ item.requester_email }}</q-item-label>
              <q-item-label caption>{{ item.question }}</q-item-label>
            </q-item-section>
            <q-item-section side>{{ item.status }}</q-item-section>
          </q-item>
        </q-list>
      </q-tab-panel>
      <q-tab-panel name="jobs">
        <q-list bordered separator>
          <q-item v-for="item in jobs" :key="item.id">
            <q-item-section>
              <q-item-label>{{ item.role_title || t('admin.leads.job') }} · {{ item.requester_email }}</q-item-label>
              <q-item-label caption>{{ item.company }}</q-item-label>
              <q-item-label caption>{{ item.role_fit_summary }}</q-item-label>
            </q-item-section>
            <q-item-section side>{{ item.status }}</q-item-section>
          </q-item>
        </q-list>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>
