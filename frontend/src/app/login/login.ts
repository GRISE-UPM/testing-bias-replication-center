import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService, Role } from '../auth/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly error = signal('');
  protected readonly roles: Role[] = ['interested', 'participant', 'organizer'];

  protected signIn(): void {
    void this.auth.loginWithCognito();
  }

  /** Development login only (backend AUTH_MODE=dev). */
  protected submit(email: string, role: string): void {
    this.error.set('');
    if (!email.trim()) {
      this.error.set('Enter an email address.');
      return;
    }
    this.auth.login(email.trim(), role as Role).subscribe({
      next: () => this.router.navigateByUrl('/experiment'),
      error: () =>
        this.error.set('The backend rejected this login. Start it with AUTH_MODE=dev.'),
    });
  }
}
