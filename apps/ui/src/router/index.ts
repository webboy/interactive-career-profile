import { createRouter, createWebHistory } from "vue-router";
import PublicLayout from "@/layouts/PublicLayout.vue";
import AdminLayout from "@/layouts/AdminLayout.vue";
import HomePage from "@/pages/public/HomePage.vue";
import PrivacyPage from "@/pages/public/PrivacyPage.vue";
import TermsPage from "@/pages/public/TermsPage.vue";
import AdminLoginPage from "@/pages/admin/AdminLoginPage.vue";
import AdminHomePage from "@/pages/admin/AdminHomePage.vue";
import AdminSettingsPage from "@/pages/admin/AdminSettingsPage.vue";
import AdminLegalPage from "@/pages/admin/AdminLegalPage.vue";
import AdminProfileItemsPage from "@/pages/admin/AdminProfileItemsPage.vue";
import AdminCareerRecordsPage from "@/pages/admin/AdminCareerRecordsPage.vue";
import AdminDocumentsPage from "@/pages/admin/AdminDocumentsPage.vue";
import AdminDocumentDetailPage from "@/pages/admin/AdminDocumentDetailPage.vue";
import AdminConversationsPage from "@/pages/admin/AdminConversationsPage.vue";
import AdminRetrievalLogsPage from "@/pages/admin/AdminRetrievalLogsPage.vue";
import AdminLeadsPage from "@/pages/admin/AdminLeadsPage.vue";
import AdminToolCallsPage from "@/pages/admin/AdminToolCallsPage.vue";
import { redirectAuthenticatedAdmin, requireAdminAuth } from "./guards";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: PublicLayout,
      children: [
        { path: "", name: "home", component: HomePage },
        { path: "privacy", name: "privacy", component: PrivacyPage },
        { path: "terms", name: "terms", component: TermsPage },
      ],
    },
    {
      path: "/admin/login",
      name: "admin-login",
      component: AdminLoginPage,
      beforeEnter: redirectAuthenticatedAdmin,
    },
    {
      path: "/admin",
      component: AdminLayout,
      beforeEnter: requireAdminAuth,
      children: [
        { path: "", name: "admin-home", component: AdminHomePage },
        { path: "settings", name: "admin-settings", component: AdminSettingsPage },
        { path: "legal", name: "admin-legal", component: AdminLegalPage },
        { path: "profile-items", name: "admin-profile-items", component: AdminProfileItemsPage },
        { path: "career-records", name: "admin-career-records", component: AdminCareerRecordsPage },
        { path: "documents", name: "admin-documents", component: AdminDocumentsPage },
        { path: "documents/:id", name: "admin-document-detail", component: AdminDocumentDetailPage },
        { path: "conversations", name: "admin-conversations", component: AdminConversationsPage },
        { path: "retrieval-logs", name: "admin-retrieval-logs", component: AdminRetrievalLogsPage },
        { path: "leads", name: "admin-leads", component: AdminLeadsPage },
        { path: "tool-calls", name: "admin-tool-calls", component: AdminToolCallsPage },
      ],
    },
  ],
});

export default router;
