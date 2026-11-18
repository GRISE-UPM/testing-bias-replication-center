import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService, ROLE_RANK, Role } from './auth.service';

/** Allows only authenticated users; visitors are sent to the login page. */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.user() ? true : inject(Router).createUrlTree(['/login']);
};

/** Allows users with at least the given role; others go to the home page (visitors to login). */
export const roleGuard =
  (minimum: Role): CanActivateFn =>
  () => {
    const user = inject(AuthService).user();
    const router = inject(Router);
    if (!user) return router.createUrlTree(['/login']);
    return ROLE_RANK[user.role] >= ROLE_RANK[minimum] ? true : router.createUrlTree(['/']);
  };
