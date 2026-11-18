import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Join } from './join';
import { Requests } from './requests';

const REQ = { id: 1, email: 'ana@uni.org', message: 'hi', status: 'pending', decided_by: null };

describe('participation', () => {
  let http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Join, Requests],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
  });

  it('join: shows the form when there is no open request and sends the message', async () => {
    const f = TestBed.createComponent(Join);
    http.expectOne('/api/participation-requests/mine').flush([]);
    await f.whenStable();
    const el = f.nativeElement as HTMLElement;
    (el.querySelector('textarea') as HTMLTextAreaElement).value = 'because';
    (el.querySelector('form') as HTMLFormElement).dispatchEvent(new Event('submit'));
    const post = http.expectOne('/api/participation-requests');
    expect(post.request.body).toEqual({ message: 'because' });
    post.flush(REQ);
    http.expectOne('/api/participation-requests/mine').flush([REQ]);
  });

  it('join: hides the form while a request is pending', async () => {
    const f = TestBed.createComponent(Join);
    http.expectOne('/api/participation-requests/mine').flush([REQ]);
    await f.whenStable();
    const el = f.nativeElement as HTMLElement;
    expect(el.querySelector('form')).toBeNull();
    expect(el.textContent).toContain('pending');
  });

  it('requests: organizer approves and the list reloads', async () => {
    const f = TestBed.createComponent(Requests);
    http.expectOne('/api/participation-requests').flush([REQ]);
    await f.whenStable();
    const el = f.nativeElement as HTMLElement;
    (el.querySelector('tbody button') as HTMLButtonElement).click();
    const d = http.expectOne('/api/participation-requests/1/decision');
    expect(d.request.body).toEqual({ approve: true });
    d.flush({ ...REQ, status: 'approved' });
    http.expectOne('/api/participation-requests').flush([{ ...REQ, status: 'approved' }]);
    await f.whenStable();
    expect(el.querySelector('tbody button')).toBeNull();
  });
});
