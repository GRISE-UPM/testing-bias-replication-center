import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface JoinRequest {
  id: number;
  email: string;
  message: string;
  status: 'pending' | 'approved' | 'rejected';
  decided_by: string | null;
}

@Injectable({ providedIn: 'root' })
export class ParticipationService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/participation-requests';

  create(message: string): Observable<JoinRequest> {
    return this.http.post<JoinRequest>(this.base, { message });
  }
  mine(): Observable<JoinRequest[]> {
    return this.http.get<JoinRequest[]>(`${this.base}/mine`);
  }
  all(): Observable<JoinRequest[]> {
    return this.http.get<JoinRequest[]>(this.base);
  }
  decide(id: number, approve: boolean): Observable<JoinRequest> {
    return this.http.post<JoinRequest>(`${this.base}/${id}/decision`, { approve });
  }
}
