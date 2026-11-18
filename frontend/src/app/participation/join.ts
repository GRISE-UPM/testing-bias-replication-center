import { Component, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { JoinRequest, ParticipationService } from './participation.service';

@Component({
  selector: 'app-join',
  templateUrl: './join.html',
  styleUrl: './participation.css',
})
export class Join {
  private readonly service = inject(ParticipationService);

  protected readonly requests = signal<JoinRequest[]>([]);
  protected readonly error = signal('');

  constructor() {
    this.refresh();
  }

  private refresh(): void {
    this.service.mine().subscribe((r) => this.requests.set(r));
  }

  protected open(): boolean {
    return this.requests().some((r) => r.status === 'pending' || r.status === 'approved');
  }

  protected submit(message: string): void {
    this.error.set('');
    this.service.create(message).subscribe({
      next: () => this.refresh(),
      error: (e: HttpErrorResponse) =>
        this.error.set(e.error?.detail ?? 'The request could not be sent.'),
    });
  }
}
