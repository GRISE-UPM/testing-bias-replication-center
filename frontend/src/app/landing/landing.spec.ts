import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Landing } from './landing';

describe('Landing', () => {
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Landing],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  const text = (el: HTMLElement, id: string) =>
    el.querySelector(`[data-testid="${id}"]`)?.textContent?.trim();

  it('shows the three figures of the simplified dashboard', async () => {
    const fixture = TestBed.createComponent(Landing);
    http.expectOne('/api/stats').flush({ experiments: 3, subjects: 72, institutions: 3 });
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;
    expect(text(el, 'experiments')).toBe('3');
    expect(text(el, 'subjects')).toBe('72');
    expect(text(el, 'institutions')).toBe('3');
  });

  it('shows a notice when the figures cannot be loaded', async () => {
    const fixture = TestBed.createComponent(Landing);
    http.expectOne('/api/stats').flush('boom', { status: 500, statusText: 'Server Error' });
    await fixture.whenStable();
    expect((fixture.nativeElement as HTMLElement).querySelector('[role="alert"]')).toBeTruthy();
  });

  it('does not require authentication to request the figures', () => {
    TestBed.createComponent(Landing);
    const req = http.expectOne('/api/stats');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({ experiments: 0, subjects: 0, institutions: 0 });
  });
});
