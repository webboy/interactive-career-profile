<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();
</script>

<template>
  <q-banner rounded class="bg-blue-1 text-primary q-mb-md">
    {{ t("chat.disclaimer") }}
  </q-banner>
</template>
