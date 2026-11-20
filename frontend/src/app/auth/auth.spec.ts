import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { AuthConfig, AuthService } from './auth.service';
import { authGuard, roleGuard } from './auth.guard';
import { authInterceptor } from './auth.interceptor';

const COGNITO: AuthConfig = {
  mode: 'cognito',
  issuer: 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST',
  clientId: 'client123',
  domain: 'https://example.auth.us-east-1.amazoncognito.com',
};

describe('auth', () => {
  let auth: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  async function init(cfg: AuthConfig | 'fail'): Promise<void> {
    const done = auth.init();
    const req = http.expectOne('/api/auth-config');
    if (cfg === 'fail') req.flush('x', { status: 503, statusText: 'Unavailable' });
    else req.flush(cfg);
    await done;
  }

  describe('development mode', () => {
    beforeEach(() => init({ mode: 'dev' }));

    it('sends the development identity only after login and only to /api', () => {
      const client = TestBed.inject(HttpClient);
      client.get('/api/stats').subscribe();
      expect(http.expectOne('/api/stats').request.headers.has('X-Dev-User')).toBe(false);

      auth.login('ana@uni.org', 'interested').subscribe();
      const me = http.expectOne('/api/me');
      expect(me.request.headers.get('X-Dev-User')).toBe('ana@uni.org:interested');
      me.flush({ email: 'ana@uni.org', role: 'interested' });

      client.get('https://other.example/x').subscribe();
      expect(http.expectOne('https://other.example/x').request.headers.has('X-Dev-User')).toBe(false);
    });

    it('forgets the user when the backend rejects the login', () => {
      auth.login('ana@uni.org', 'interested').subscribe({ error: () => undefined });
      http.expectOne('/api/me').flush('no', { status: 401, statusText: 'Unauthorized' });
      expect(auth.user()).toBeNull();
    });

    it('logout clears the session', () => {
      auth.login('ana@uni.org', 'organizer').subscribe();
      http.expectOne('/api/me').flush({ email: 'ana@uni.org', role: 'organizer' });
      auth.logout();
      expect(auth.user()).toBeNull();
      expect(auth.devHeader()).toBeNull();
    });

    it('guard sends visitors to the login page and lets users through', () => {
      const router = TestBed.inject(Router);
      const run = () => TestBed.runInInjectionContext(() => authGuard({} as never, {} as never));
      expect(router.serializeUrl(run() as never)).toBe('/login');
      auth.login('ana@uni.org', 'interested').subscribe();
      http.expectOne('/api/me').flush({});
      expect(run()).toBe(true);
    });

    it('role guard keeps interested researchers out of organizer pages', () => {
      const router = TestBed.inject(Router);
      auth.login('ana@uni.org', 'interested').subscribe();
      http.expectOne('/api/me').flush({});
      const run = () =>
        TestBed.runInInjectionContext(() => roleGuard('organizer')({} as never, {} as never));
      expect(router.serializeUrl(run() as never)).toBe('/');
    });
  });

  describe('cognito mode', () => {
    beforeEach(() => init(COGNITO));

    it('starts signed out and shows the Cognito mode', () => {
      expect(auth.mode()).toBe('cognito');
      expect(auth.user()).toBeNull();
      expect(auth.accessToken()).toBeNull();
    });

    it('sends the access token as Bearer to /api only, never to other hosts', () => {
      (auth as unknown as { token: string }).token = 'abc.def.ghi';
      const client = TestBed.inject(HttpClient);

      client.get('/api/me').subscribe();
      const me = http.expectOne('/api/me');
      expect(me.request.headers.get('Authorization')).toBe('Bearer abc.def.ghi');
      expect(me.request.headers.has('X-Dev-User')).toBe(false);

      client.get('https://other.example/x').subscribe();
      expect(http.expectOne('https://other.example/x').request.headers.has('Authorization')).toBe(false);

      client.get('/api/auth-config').subscribe();
      expect(http.expectOne('/api/auth-config').request.headers.has('Authorization')).toBe(false);
    });

    it('does not use the development identity', () => {
      expect(auth.devHeader()).toBeNull();
    });
  });

  it('falls back to signed-out when the backend has no sign-in configuration', async () => {
    await init('fail');
    expect(auth.mode()).toBe('off');
    expect(auth.user()).toBeNull();
  });
});
