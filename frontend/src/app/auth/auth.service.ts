import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom, Observable, tap } from 'rxjs';
import { User as OidcUser, UserManager, WebStorageStateStore } from 'oidc-client-ts';

export type Role = 'interested' | 'participant' | 'organizer';
export interface SessionUser {
  email: string;
  role: Role;
}
/** How the backend wants users to sign in (GET /api/auth-config). */
export type AuthConfig =
  | { mode: 'off' | 'dev' }
  | { mode: 'cognito'; issuer: string; clientId: string; domain: string };

const DEV_KEY = 'dev-user';
export const ROLE_RANK: Record<Role, number> = { interested: 1, participant: 2, organizer: 3 };

/**
 * Current session. In `cognito` mode the user signs in at the Amazon Cognito Hosted UI
 * (authorization code + PKCE, decision D6) and the Access Token is sent to the API as a
 * Bearer token. The `dev` mode is a development-only fallback (backend AUTH_MODE=dev).
 * Components depend only on `user()`; the role always comes from the backend (`/api/me`).
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private config: AuthConfig = { mode: 'off' };
  private manager: UserManager | null = null;
  private token: string | null = null;

  readonly mode = signal<AuthConfig['mode']>('off');
  readonly user = signal<SessionUser | null>(null);

  /** Runs before the first navigation: reads the sign-in mode and restores or completes the session. */
  async init(): Promise<void> {
    try {
      this.config = await firstValueFrom(this.http.get<AuthConfig>('/api/auth-config'));
    } catch {
      this.config = { mode: 'off' };
    }
    this.mode.set(this.config.mode);
    if (this.config.mode === 'dev') {
      this.user.set(this.restoreDev());
    } else if (this.config.mode === 'cognito') {
      await this.initCognito(this.config);
    }
  }

  /** Access Token for the API, or null when nobody is signed in with Cognito. */
  accessToken(): string | null {
    return this.token;
  }

  /** Header value for the backend's development mode; null when nobody is logged in. */
  devHeader(): string | null {
    const u = this.mode() === 'dev' ? this.user() : null;
    return u ? `${u.email}:${u.role}` : null;
  }

  /** Redirects to the Cognito Hosted UI. */
  loginWithCognito(): Promise<void> {
    return this.manager ? this.manager.signinRedirect() : Promise.resolve();
  }

  /** Development login only. */
  login(email: string, role: Role): Observable<SessionUser> {
    this.setDev({ email, role });
    return this.http.get<SessionUser>('/api/me').pipe(tap({ error: () => this.setDev(null) }));
  }

  logout(): void {
    this.token = null;
    this.user.set(null);
    this.setDev(null);
    if (this.manager && this.config.mode === 'cognito') {
      const { clientId, domain } = this.config;
      void this.manager.removeUser().finally(() => {
        const back = encodeURIComponent(window.location.origin);
        window.location.assign(`${domain}/logout?client_id=${clientId}&logout_uri=${back}`);
      });
    }
  }

  private async initCognito(c: Extract<AuthConfig, { mode: 'cognito' }>): Promise<void> {
    this.manager = new UserManager({
      authority: c.issuer,
      client_id: c.clientId,
      redirect_uri: window.location.origin + '/',
      response_type: 'code',
      scope: 'openid email profile',
      userStore: new WebStorageStateStore({ store: window.localStorage }),
      automaticSilentRenew: true,
    });
    this.manager.events.addUserLoaded((u) => {
      this.token = u.access_token;
    });
    this.manager.events.addAccessTokenExpired(() => this.clearSession());
    this.manager.events.addUserUnloaded(() => this.clearSession());
    try {
      let oidcUser: OidcUser | null | undefined;
      const params = new URLSearchParams(window.location.search);
      if (params.has('code') && params.has('state')) {
        oidcUser = await this.manager.signinCallback();
        window.history.replaceState(null, '', '/experiment');
      } else {
        oidcUser = await this.manager.getUser();
      }
      if (oidcUser && !oidcUser.expired) {
        this.token = oidcUser.access_token;
        this.user.set(await firstValueFrom(this.http.get<SessionUser>('/api/me')));
      }
    } catch {
      this.clearSession(); // invalid callback or backend refusal: stay signed out
    }
  }

  private clearSession(): void {
    this.token = null;
    this.user.set(null);
  }

  private setDev(u: SessionUser | null): void {
    this.user.set(u);
    try {
      if (u) localStorage.setItem(DEV_KEY, JSON.stringify(u));
      else localStorage.removeItem(DEV_KEY);
    } catch {
      /* storage unavailable: the session lives only in memory */
    }
  }

  private restoreDev(): SessionUser | null {
    try {
      const raw = localStorage.getItem(DEV_KEY);
      return raw ? (JSON.parse(raw) as SessionUser) : null;
    } catch {
      return null;
    }
  }
}
