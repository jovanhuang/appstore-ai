import { api } from 'src/boot/axios';
import { defineStore } from 'pinia';
import jwt_decode from 'jwt-decode';
import { Cookies, useQuasar, Notify } from 'quasar';

export enum Role {
  user = 'user',
  admin = 'admin',
}
export interface User {
  userId: string | null;
  name: string | null;
  role: Role;
}

export interface LoginResponse {
  access_token: string; // JWT
  refresh_token: string;
  token_type: string; // bearer
}

export interface JWT {
  sub: string; // userId
  name: string;
  role: Role;
}

// TODO: Fix storing the access token in a secured way that Axios can use for the OAuth
// currently have to store accesstoken in Cookie that is not secured (httponly)

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    returnUrl: null as string | null,
  }),
  actions: {
    async login(userId: string, password: string): Promise<void> {
      try {
        const creds = new FormData();
        creds.append('username', userId);
        creds.append('password', password);
        const response = await api.post('/auth/', creds);
        // Decode JWT
        const { access_token, refresh_token }: LoginResponse = response.data;
        const jwt_data = jwt_decode(access_token) as JWT;

        if (!jwt_data) {
          console.error('Failed to decode');
        }
        this.user = {
          // TODO: Replace with actual api call
          userId: jwt_data.sub,
          name: jwt_data.name,
          role: jwt_data.role,
        } as User;
      } catch (err) {
        Notify.create({
          type: 'negative',
          position: 'top',
          message: 'Failed to login',
        });
      }
      this.router.push(this.returnUrl || '/');
    },
    logout(): void {
      try {
        const response = api.delete('/auth/logout');
        this.user = null;
        localStorage.removeItem('auth');
        this.router.push({ name: 'Login' });
      } catch (err) {
        console.warn('Logout failed');
      }
    },
    async refresh(): Promise<void> {
      console.warn('Refreshing access token');
      try {
        const response = await api.post('/auth/refresh', {
          grant_type: 'refresh_token'
        });
        location.reload()
      } catch (err) {
        console.error(err);
      }
    },
  },
  persist: {
    storage: localStorage,
    paths: ['user', 'returnUrl'],
  },
});
