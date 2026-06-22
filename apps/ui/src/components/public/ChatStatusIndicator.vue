<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { ChatJobPhase } from "@/stores/publicChatTypes";

defineProps<{
  phase: ChatJobPhase;
}>();

const { t } = useI18n();
</script>

<template>
  <div v-if="phase !== 'idle'" class="q-mb-md">
    <q-banner rounded class="bg-grey-3">
      <template #avatar>
        <q-spinner-dots color="primary" />
      </template>
      {{
        phase === "submitting"
          ? t("chat.statusSubmitting")
          : phase === "queued"
            ? t("chat.statusQueued")
            : t("chat.statusProcessing")
      }}
    </q-banner>
  </div>
</template>
