import { Component, inject, signal } from '@angular/core';
import { JoinRequest, ParticipationService } from './participation.service';

@Component({
  selector: 'app-requests',
  templateUrl: './requests.html',
  styleUrl: './participation.css',
})
export class Requests {
  private readonly service = inject(ParticipationService);
  protected readonly requests = signal<JoinRequest[]>([]);
  protected readonly failed = signal(false);

  constructor() {
    this.load();
  }

  private load(): void {
    this.service.all().subscribe({
      next: (r) => this.requests.set(r),
      error: () => this.failed.set(true),
    });
  }

  protected decide(id: number, approve: boolean): void {
    this.service.decide(id, approve).subscribe({ next: () => this.load(), error: () => this.failed.set(true) });
  }
}
