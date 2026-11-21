import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

/** Identifies the user to our own API (never to other hosts): Bearer token, or the dev header. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith('/api') || req.url === '/api/auth-config') return next(req);
  const auth = inject(AuthService);
  const token = auth.accessToken();
  if (token) return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
  const dev = auth.devHeader();
  return next(dev ? req.clone({ setHeaders: { 'X-Dev-User': dev } }) : req);
};
