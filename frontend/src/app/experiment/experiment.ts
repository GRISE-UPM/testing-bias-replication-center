import { Component, inject, signal } from '@angular/core';
import { ExperimentDetails, ExperimentService } from './experiment.service';

@Component({
  selector: 'app-experiment',
  templateUrl: './experiment.html',
  styleUrl: './experiment.css',
})
export class Experiment {
  private readonly service = inject(ExperimentService);

  protected readonly details = signal<ExperimentDetails | null>(null);
  protected readonly failed = signal(false);
  protected readonly emailStatus = signal<'idle' | 'sent' | 'error'>('idle');

  constructor() {
    this.service.get().subscribe({
      next: (d) => this.details.set(d),
      error: () => this.failed.set(true),
    });
  }

  protected emailMe(): void {
    this.service.emailMe().subscribe({
      next: () => this.emailStatus.set('sent'),
      error: () => this.emailStatus.set('error'),
    });
  }
}
