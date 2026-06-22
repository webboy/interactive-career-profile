<script setup lang="ts">
import LegalPageView from "@/components/public/LegalPageView.vue";
import { getTermsPage } from "@/api/public";
</script>

<template>
  <q-page padding>
    <LegalPageView :fetch-page="getTermsPage" />
  </q-page>
</template>
