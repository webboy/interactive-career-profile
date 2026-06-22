<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { getConversationMessages, listConversations } from "@/api/admin";
import type { ConversationListItem, ConversationMessage } from "@/api/adminTypes";
import AdminLoadingError from "@/components/admin/AdminLoadingError.vue";
import AdminPageHeader from "@/components/admin/AdminPageHeader.vue";

const { t } = useI18n();
const conversations = ref<ConversationListItem[]>([]);
const selectedId = ref<number | null>(null);
const messages = ref<ConversationMessage[]>([]);
const loading = ref(true);
const messagesLoading = ref(false);
const error = ref<string | null>(null);

async function loadConversations(): Promise<void> {
  loading.value = true;
  error.value = null;
  try {
    conversations.value = await listConversations();
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    loading.value = false;
  }
}

async function openConversation(id: number): Promise<void> {
  selectedId.value = id;
  messagesLoading.value = true;
  try {
    const response = await getConversationMessages(id);
    messages.value = response.messages;
  } catch (err) {
    error.value = err instanceof Error ? err.message : t("app.error");
  } finally {
    messagesLoading.value = false;
  }
}

onMounted(() => void loadConversations());
</script>

<template>
  <q-page padding>
    <AdminPageHeader :title="t('admin.nav.conversations')" />
    <AdminLoadingError :loading="loading" :error="error" />

    <div v-if="!loading" class="row q-col-gutter-md">
      <div class="col-12 col-md-5">
        <q-list bordered separator>
          <q-item
            v-for="conversation in conversations"
            :key="conversation.id"
            clickable
            :active="selectedId === conversation.id"
            @click="openConversation(conversation.id)"
          >
            <q-item-section>
              <q-item-label>#{{ conversation.id }} · {{ conversation.message_count }} msgs</q-item-label>
              <q-item-label caption>{{ conversation.latest_message_preview }}</q-item-label>
              <q-item-label caption>{{ conversation.session_id }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </div>
      <div class="col-12 col-md-7">
        <q-banner v-if="messagesLoading" rounded class="bg-grey-3">{{ t('app.loading') }}</q-banner>
        <q-list v-else-if="messages.length" bordered separator>
          <q-item v-for="message in messages" :key="message.id">
            <q-item-section>
              <q-item-label>{{ message.role }}</q-item-label>
              <q-item-label caption class="message-content">{{ message.content }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
        <q-banner v-else rounded class="bg-grey-2">{{ t('admin.selectConversation') }}</q-banner>
      </div>
    </div>
  </q-page>
</template>

<style scoped>
.message-content {
  white-space: pre-wrap;
}
</style>
