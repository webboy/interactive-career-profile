<script setup lang="ts">
import { onMounted } from "vue";
import { useI18n } from "vue-i18n";
import ChatComposer from "@/components/public/ChatComposer.vue";
import ChatDisclaimerBanner from "@/components/public/ChatDisclaimerBanner.vue";
import ChatMessageList from "@/components/public/ChatMessageList.vue";
import ChatStatusIndicator from "@/components/public/ChatStatusIndicator.vue";
import LeadPromptCards from "@/components/public/LeadPromptCards.vue";
import { usePublicChatStore } from "@/stores/publicChat";
import { usePublicSettingsStore } from "@/stores/publicSettings";

const { t } = useI18n();
const settingsStore = usePublicSettingsStore();
const chatStore = usePublicChatStore();

onMounted(() => {
  void settingsStore.loadSettings();
});

async function handleSend(message: string): Promise<void> {
  await chatStore.sendMessage(message);
}

async function handleLeadPrompt(prompt: string): Promise<void> {
  await chatStore.sendMessage(prompt);
}
</script>

<template>
  <q-page padding>
    <div class="q-gutter-md">
      <h1 class="text-h4">{{ settingsStore.appName }}</h1>
      <p>{{ t("app.homeIntro") }}</p>

      <q-banner v-if="settingsStore.loading" rounded class="bg-grey-3">
        {{ t("app.loading") }}
      </q-banner>
      <q-banner v-else-if="settingsStore.error" rounded class="bg-red-1 text-negative">
        {{ settingsStore.error }}
      </q-banner>

      <template v-else>
        <ChatDisclaimerBanner />
        <LeadPromptCards @select="handleLeadPrompt" />
        <ChatMessageList :messages="chatStore.messages" />
        <ChatStatusIndicator :phase="chatStore.jobPhase" />
        <q-banner v-if="chatStore.lastError" rounded class="bg-red-1 text-negative">
          {{ chatStore.lastError }}
        </q-banner>
        <ChatComposer :disabled="chatStore.isBusy" @send="handleSend" />
      </template>
    </div>
  </q-page>
</template>
