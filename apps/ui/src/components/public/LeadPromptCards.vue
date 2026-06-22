<script setup lang="ts">
import { useI18n } from "vue-i18n";

const emit = defineEmits<{
  select: [prompt: string];
}>();

const { t } = useI18n();

const prompts = [
  {
    key: "meeting",
    labelKey: "chat.leadMeeting",
    textKey: "chat.leadMeetingPrompt",
  },
  {
    key: "job",
    labelKey: "chat.leadJob",
    textKey: "chat.leadJobPrompt",
  },
  {
    key: "followUp",
    labelKey: "chat.leadFollowUp",
    textKey: "chat.leadFollowUpPrompt",
  },
] as const;

function usePrompt(textKey: (typeof prompts)[number]["textKey"]): void {
  emit("select", t(textKey));
}
</script>

<template>
  <div class="q-mb-md">
    <div class="text-subtitle2 q-mb-sm">{{ t("chat.leadPromptsHeading") }}</div>
    <div class="row q-col-gutter-sm">
      <div v-for="prompt in prompts" :key="prompt.key" class="col-12 col-md-4">
        <q-btn
          outline
          color="primary"
          class="full-width"
          :label="t(prompt.labelKey)"
          @click="usePrompt(prompt.textKey)"
        />
      </div>
    </div>
  </div>
</template>
