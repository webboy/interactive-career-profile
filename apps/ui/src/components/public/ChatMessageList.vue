<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { ChatMessage } from "@/stores/publicChatTypes";
import ChatSourceLabels from "@/components/public/ChatSourceLabels.vue";

defineProps<{
  messages: ChatMessage[];
}>();

const { t } = useI18n();
</script>

<template>
  <div class="chat-message-list q-gutter-md">
    <q-banner v-if="messages.length === 0" rounded class="bg-grey-2">
      {{ t("chat.emptyState") }}
    </q-banner>

    <div
      v-for="message in messages"
      :key="message.id"
      class="row"
      :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
    >
      <q-card
        flat
        bordered
        :class="[
          'chat-bubble q-pa-md',
          message.role === 'user' ? 'bg-primary text-white' : 'bg-grey-2',
          message.refused ? 'border-negative' : '',
          message.failed ? 'border-negative bg-red-1' : '',
        ]"
        style="max-width: 85%"
      >
        <div class="text-body2">{{ message.text }}</div>
        <div v-if="message.refused" class="text-caption q-mt-xs text-negative">
          {{ t("chat.refusedHint") }}
        </div>
        <ChatSourceLabels
          v-if="message.role === 'assistant' && message.sources?.length"
          :sources="message.sources"
        />
      </q-card>
    </div>
  </div>
</template>

<style scoped>
.chat-bubble {
  white-space: pre-wrap;
}
</style>
