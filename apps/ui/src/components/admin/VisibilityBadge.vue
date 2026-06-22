<script setup lang="ts">
import { computed } from "vue";
import type { Visibility } from "@/api/adminTypes";

const props = defineProps<{
  visibility: Visibility | string;
}>();

const color = computed(() => {
  switch (props.visibility) {
    case "public":
      return "positive";
    case "private":
      return "warning";
    case "draft":
      return "info";
    case "archived":
      return "grey";
    default:
      return "primary";
  }
});
</script>

<template>
  <q-badge :color="color" :label="visibility" />
</template>
