<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps<{
  disabled?: boolean;
}>();

const emit = defineEmits<{
  send: [message: string];
}>();

const { t } = useI18n();
const draft = ref("");

function submit(): void {
  const text = draft.value.trim();
  if (!text || props.disabled) {
    return;
  }
  emit("send", text);
  draft.value = "";
}
</script>

<template>
  <div class="row q-col-gutter-sm items-end">
    <div class="col">
      <q-input
        v-model="draft"
        type="textarea"
        autogrow
        :label="t('chat.inputPlaceholder')"
        :disable="disabled"
        @keyup.enter.exact.prevent="submit"
      />
    </div>
    <div class="col-auto">
      <q-btn color="primary" :label="t('chat.send')" :disable="disabled" @click="submit" />
    </div>
  </div>
</template>
