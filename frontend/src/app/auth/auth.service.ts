import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

export type Role = 'interested' | 'participant' | 'organizer';
export interface SessionUser {
  email: string;
  role: Role;
}

const KEY = 'dev-user';

/**
 * TEMPORARY development session. It only remembers the user chosen on the dev login page.
 * It will be replaced by Amazon Cognito (decision D6); components depend only on `user()`.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  readonly user = signal<SessionUser | null>(this.restore());

  /** Header value for the backend's development mode; null when nobody is logged in. */
  devHeader(): string | null {
    const u = this.user();
    return u ? `${u.email}:${u.role}` : null;
  }

  login(email: string, role: Role): Observable<SessionUser> {
    const candidate: SessionUser = { email, role };
    this.set(candidate);
    return this.http.get<SessionUser>('/api/me').pipe(
      tap({
        error: () => this.set(null),
      }),
    );
  }

  logout(): void {
    this.set(null);
  }

  private set(u: SessionUser | null): void {
    this.user.set(u);
    try {
      if (u) localStorage.setItem(KEY, JSON.stringify(u));
      else localStorage.removeItem(KEY);
    } catch {
      /* storage unavailable: the session lives only in memory */
    }
  }

  private restore(): SessionUser | null {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? (JSON.parse(raw) as SessionUser) : null;
    } catch {
      return null;
    }
  }
}
