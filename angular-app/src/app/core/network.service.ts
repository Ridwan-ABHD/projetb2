import { Injectable, inject, signal } from '@angular/core';
import { OfflineQueueService } from './offline-queue.service';

@Injectable({ providedIn: 'root' })
export class NetworkService {
  private queue = inject(OfflineQueueService);

  readonly isOnline = signal(navigator.onLine);
  readonly lastDataAt = signal<Date | null>(null);

  constructor() {
    window.addEventListener('online', () => {
      this.isOnline.set(true);
      this.queue.flush();
    });
    window.addEventListener('offline', () => this.isOnline.set(false));
  }

  markDataFresh(): void {
    this.lastDataAt.set(new Date());
  }
}
