import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { AuthService } from './auth.service';
import { authGuard } from './auth.guard';
import { devAuthInterceptor } from './dev-auth.interceptor';

describe('auth', () => {
  let auth: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([devAuthInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    auth = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

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
});
