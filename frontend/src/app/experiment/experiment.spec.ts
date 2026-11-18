import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Experiment } from './experiment';

const DETAILS = {
  title: 'T',
  summary: 'S',
  description: 'D',
  papers: [{ title: 'Paper A', authors: 'X', venue: 'V', year: 2026, url: 'https://p' }],
  demos: [{ title: 'Demo 1', url: 'https://d' }],
};

describe('Experiment', () => {
  let http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Experiment],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  it('shows the papers before the description', async () => {
    const f = TestBed.createComponent(Experiment);
    http.expectOne('/api/experiment').flush(DETAILS);
    await f.whenStable();
    const el = f.nativeElement as HTMLElement;
    const text = el.textContent ?? '';
    expect(text).toContain('Paper A');
    expect(text.indexOf('Papers from the project')).toBeLessThan(text.indexOf('About the experiment'));
    expect(el.querySelector('a[href="https://d"]')).toBeTruthy();
  });

  it('asks the backend to email the information', async () => {
    const f = TestBed.createComponent(Experiment);
    http.expectOne('/api/experiment').flush(DETAILS);
    await f.whenStable();
    ((f.nativeElement as HTMLElement).querySelector('button') as HTMLButtonElement).click();
    http.expectOne('/api/experiment/email').flush({}, { status: 202, statusText: 'Accepted' });
    await f.whenStable();
    expect((f.nativeElement as HTMLElement).querySelector('[role="status"]')).toBeTruthy();
  });

  it('shows a notice when the details cannot be loaded', async () => {
    const f = TestBed.createComponent(Experiment);
    http.expectOne('/api/experiment').flush('x', { status: 500, statusText: 'Error' });
    await f.whenStable();
    expect((f.nativeElement as HTMLElement).querySelector('[role="alert"]')).toBeTruthy();
  });
});
