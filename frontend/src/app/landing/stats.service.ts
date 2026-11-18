import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface PublicStats {
  experiments: number;
  subjects: number;
  institutions: number;
}

@Injectable({ providedIn: 'root' })
export class StatsService {
  private readonly http = inject(HttpClient);

  getPublicStats(): Observable<PublicStats> {
    return this.http.get<PublicStats>('/api/stats');
  }
}
