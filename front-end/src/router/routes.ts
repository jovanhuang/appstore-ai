import AdminDashboardLayout from 'src/layouts/AdminDashboardLayout.vue';
import AdminDashboardPage from 'src/pages/admin/AdminDashboardPage.vue';
import AdminLoginPage from 'src/pages/admin/AdminLoginPage.vue';
import AdminModelsPage from 'src/pages/admin/AdminModelsPage.vue';
import CreateModel from 'src/pages/models/ModelCreate.vue';
import DashboardLayout from 'src/layouts/DashboardLayout.vue';
import DashboardPage from 'src/pages/DashboardPage.vue';
import ErrorNotFound from 'src/pages/ErrorNotFound.vue';
import LoginLayout from 'src/layouts/LoginLayout.vue';
import LoginPage from 'src/pages/auth/LoginPage.vue';
import MainLayout from 'src/layouts/MainLayout.vue';
import ModelInferenceServiceEdit from 'src/pages/models/ModelInferenceServiceEdit.vue';
import ModelMetadataEdit from 'src/pages/models/ModelMetadataEdit.vue';
import ModelPage from 'src/pages/models/ModelPage.vue';
import ModelVideoEdit from 'src/pages/models/ModelVideoEdit.vue';
import SearchLayout from 'src/layouts/SearchLayout.vue';
import SearchModelsPage from 'src/pages/models/SearchModelsPage.vue';

import { Notify } from 'quasar';
import { RouteRecordRaw } from 'vue-router';
import { useAuthStore } from 'src/stores/auth-store';

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: LoginLayout,
    children: [
      {
        path: '',
        name: 'Login',
        component: LoginPage,
        beforeEnter: () => {
          const auth = useAuthStore();
          if (auth.user?.userId) {
            // Logged in
            return '/';
          }
        },
      },
      {
        path: 'admin',
        name: 'Admin Login',
        beforeEnter: () => {
          const auth = useAuthStore();
          if (auth.user?.role == 'admin') {
            // Logged in
            return '/admin';
          }
        },
        component: AdminLoginPage,
      },
    ],
  },
  {
    path: '/admin',
    component: AdminDashboardLayout,
    children: [
      {
        path: '',
        name: 'Admin Dashboard',
        component: AdminDashboardPage,
        beforeEnter: () => {
          const auth = useAuthStore();
          if (auth.user?.role != 'admin') {
            auth.logout();
            Notify.create({
              type: 'warning',
              position: 'top',
              message: 'This account does not have sufficient privileges',
            });
            return '/login/admin';
          }
        },
      },
      {
        path: 'models',
        name: 'Admin Models Check Page',
        component: AdminModelsPage,
        beforeEnter: () => {
          const auth = useAuthStore();
          if (auth.user?.role != 'admin') {
            auth.logout();
            Notify.create({
              type: 'warning',
              position: 'top',
              message: 'This account does not have sufficient privileges',
            });
            return '/login/admin';
          }
        },
      },
    ],
  },
  {
    path: '/model',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Model',
        component: SearchModelsPage,
        beforeEnter: () => {
          // Redirect to search page filtered by user
          return {
            name: 'Models',
          };
        },
      },
      {
        path: ':userId',
        component: SearchModelsPage,
        beforeEnter: (to) => {
          // Redirect to search page filtered by user
          return {
            name: 'Models',
            query: {
              creator: to.params.userId,
            },
          };
        },
      },
      {
        path: ':userId/:modelId/edit',
        beforeEnter: (to) => {
          const auth = useAuthStore();
          if (auth.user?.userId !== to.params.userId) {
            // Check if user is the owner of the model
            return '/';
          }
        },
        children: [
          {
            path: '',
            name: 'Edit',
            redirect: 'metadata',
          },
          {
            path: 'metadata',
            name: 'Model Metadata',
            component: ModelMetadataEdit,
          },
          {
            path: 'inference',
            name: 'Model Inference Service',
            component: ModelInferenceServiceEdit,
          },
          {
            path: 'video',
            name: 'Model Example Video',
            component: ModelVideoEdit,
          },
        ],
      },

      {
        path: ':userId/:modelId',
        component: ModelPage,
      },
      {
        path: 'create',
        name: 'Create Model',
        component: CreateModel,
      },
    ],
  },
  {
    path: '/models',
    component: SearchLayout,
    children: [
      {
        path: '',
        name: 'Models',
        component: SearchModelsPage,
      },
      {
        path: ':userId',
        component: SearchModelsPage,
        beforeEnter: (to) => {
          // Redirect to search page filtered by user
          return {
            name: 'Models',
            query: {
              creator: to.params.userId,
            },
          };
        },
      },
    ],
  },
  {
    path: '/',
    component: DashboardLayout,
    children: [{ path: '', name: 'Dashboard', component: DashboardPage }],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: ErrorNotFound,
  },
];

export default routes;
