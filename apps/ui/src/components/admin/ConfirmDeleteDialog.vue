<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  title?: string;
}>();

const emit = defineEmits<{
  confirm: [];
}>();

const open = ref(false);

function show(): void {
  open.value = true;
}

function confirm(): void {
  emit("confirm");
  open.value = false;
}

defineExpose({ show });
</script>

<template>
  <q-dialog v-model="open">
    <q-card style="min-width: 320px">
      <q-card-section>
        <div class="text-h6">{{ title || $t("admin.confirmDelete") }}</div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat :label="$t('admin.cancel')" v-close-popup />
        <q-btn color="negative" :label="$t('admin.delete')" @click="confirm" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
