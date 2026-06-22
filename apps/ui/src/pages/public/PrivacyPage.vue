<script setup lang="ts">
import LegalPageView from "@/components/public/LegalPageView.vue";
import { getPrivacyPage } from "@/api/public";
</script>

<template>
  <q-page padding>
    <LegalPageView :fetch-page="getPrivacyPage" />
  </q-page>
</template>
