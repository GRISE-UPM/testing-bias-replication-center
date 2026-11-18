import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface Paper { title: string; authors: string; venue: string; year: number; url: string }
export interface Demo { title: string; url: string }
export interface ExperimentDetails {
  title: string;
  summary: string;
  description: string;
  papers: Paper[];
  demos: Demo[];
}

@Injectable({ providedIn: 'root' })
export class ExperimentService {
  private readonly http = inject(HttpClient);

  get(): Observable<ExperimentDetails> {
    return this.http.get<ExperimentDetails>('/api/experiment');
  }

  emailMe(): Observable<unknown> {
    return this.http.post('/api/experiment/email', {});
  }
}
