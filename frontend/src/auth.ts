import { User } from './types';

const SESSION_KEY = 'konimex_sl_mtm_user_session';

export class AuthController {
  private currentUser: User | null = null;

  constructor() {
    this.initSessionGuard();
    this.loadSession();
  }

  private initSessionGuard(): void {
    // Auto logout when browser tab is closed
    window.addEventListener('beforeunload', () => {
      // Clear session when leaving/closing tab
      this.clearSession();
    });
  }

  public async login(usernameInput: string, passwordInput: string, apiBaseUrl: string = ''): Promise<User> {
    const res = await fetch(`${apiBaseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: usernameInput, password: passwordInput })
    });

    const data = await res.json();
    if (!res.ok || data.status !== 'success') {
      throw new Error(data.message || 'Login gagal! Periksa kredensial Anda.');
    }

    const user: User = data.user;
    user.token = data.token;
    
    this.saveSession(user);
    return user;
  }

  public saveSession(user: User): void {
    this.currentUser = user;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
  }

  public loadSession(): User | null {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) {
      try {
        this.currentUser = JSON.parse(raw);
        return this.currentUser;
      } catch (e) {
        this.clearSession();
      }
    }
    return null;
  }

  public clearSession(): void {
    this.currentUser = null;
    sessionStorage.removeItem(SESSION_KEY);
  }

  public getCurrentUser(): User | null {
    return this.currentUser || this.loadSession();
  }

  public isAuthenticated(): boolean {
    return this.getCurrentUser() !== null;
  }

  public isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user ? user.role === 'admin' : false;
  }
}
