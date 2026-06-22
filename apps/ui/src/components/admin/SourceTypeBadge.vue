<script setup lang="ts">
import { computed } from "vue";
import { formatSourceType } from "@/utils/format";

const props = defineProps<{
  sourceType: string;
}>();

const label = computed(() => formatSourceType(props.sourceType));
</script>

<template>
  <q-badge color="secondary" outline :label="label" />
</template>
