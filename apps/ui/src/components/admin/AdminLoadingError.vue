<script setup lang="ts">
defineProps<{
  loading?: boolean;
  error?: string | null;
}>();
</script>

<template>
  <q-banner v-if="loading" rounded class="bg-grey-3 q-mb-md">{{ $t("app.loading") }}</q-banner>
  <q-banner v-else-if="error" rounded class="bg-red-1 text-negative q-mb-md">{{ error }}</q-banner>
</template>
