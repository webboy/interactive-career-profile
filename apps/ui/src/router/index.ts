import { createRouter, createWebHistory } from "vue-router";
import PublicLayout from "@/layouts/PublicLayout.vue";
import AdminLayout from "@/layouts/AdminLayout.vue";
import HomePage from "@/pages/public/HomePage.vue";
import PrivacyPage from "@/pages/public/PrivacyPage.vue";
import TermsPage from "@/pages/public/TermsPage.vue";
import AdminLoginPage from "@/pages/admin/AdminLoginPage.vue";
import AdminHomePage from "@/pages/admin/AdminHomePage.vue";
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
      ],
    },
  ],
});

export default router;
