import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

/** TEMPORARY: sends the development identity to the backend. Removed with Cognito. */
export const devAuthInterceptor: HttpInterceptorFn = (req, next) => {
  const header = inject(AuthService).devHeader();
  return next(header && req.url.startsWith('/api') ? req.clone({ setHeaders: { 'X-Dev-User': header } }) : req);
};
