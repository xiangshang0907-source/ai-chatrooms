// 认证服务
import { AuthResponse, User } from './types';

class AuthService {
  private readonly TOKEN_KEY = 'ai_chatrooms_token';
  private readonly REFRESH_TOKEN_KEY = 'ai_chatrooms_refresh_token';
  private readonly USER_KEY = 'ai_chatrooms_user';

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '登录失败');
    }

    const data: AuthResponse = await response.json();
    this.setAuth(data);
    return data;
  }

  async register(username: string, email: string, password: string, displayName?: string): Promise<AuthResponse> {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        email,
        password,
        display_name: displayName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '注册失败');
    }

    const data: AuthResponse = await response.json();
    this.setAuth(data);
    return data;
  }

  async logout(): Promise<void> {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  private setAuth(auth: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, auth.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, auth.refresh_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(auth.user));
  }

  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('没有刷新令牌');
    }

    const response = await fetch('/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      await this.logout();
      throw new Error('令牌刷新失败');
    }

    const data = await response.json();
    localStorage.setItem(this.TOKEN_KEY, data.access_token);
    return data;
  }

  async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getToken();
    if (!token) {
      throw new Error('用户未登录');
    }

    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // 如果token过期，尝试刷新
    if (response.status === 401) {
      try {
        await this.refreshToken();
        const newToken = this.getToken();
        const retryResponse = await fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${newToken}`,
            'Content-Type': 'application/json',
          },
        });
        return retryResponse;
      } catch {
        await this.logout();
        throw new Error('认证失败，请重新登录');
      }
    }

    return response;
  }
}

export const authService = new AuthService();
