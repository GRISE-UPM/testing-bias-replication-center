import { Component, inject, signal } from '@angular/core';
import { PublicStats, StatsService } from './stats.service';

@Component({
  selector: 'app-landing',
  templateUrl: './landing.html',
  styleUrl: './landing.css',
})
export class Landing {
  private readonly statsService = inject(StatsService);

  protected readonly stats = signal<PublicStats | null>(null);
  protected readonly failed = signal(false);

  constructor() {
    this.statsService.getPublicStats().subscribe({
      next: (s) => this.stats.set(s),
      error: () => this.failed.set(true),
    });
  }
}
