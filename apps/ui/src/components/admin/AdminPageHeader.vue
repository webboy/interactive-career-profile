<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="q-mb-md">
    <div class="text-h5">{{ title }}</div>
    <div v-if="subtitle" class="text-body2 text-grey-7">{{ subtitle }}</div>
  </div>
</template>
