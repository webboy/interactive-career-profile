<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { formatSourceType } from "@/utils/format";

defineProps<{
  sources: { source_type: string; title: string }[];
}>();

const { t } = useI18n();
const expanded = ref(false);
</script>

<template>
  <q-expansion-item
    v-if="sources.length"
    v-model="expanded"
    dense
    :label="t('chat.sourcesHeading', { count: sources.length })"
    header-class="text-caption text-grey-8"
    class="q-mt-xs"
  >
    <q-list dense bordered class="rounded-borders">
      <q-item v-for="(source, index) in sources" :key="`${source.source_type}-${source.title}-${index}`">
        <q-item-section>
          <q-item-label caption>{{ formatSourceType(source.source_type) }}</q-item-label>
          <q-item-label>{{ source.title }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-expansion-item>
</template>
