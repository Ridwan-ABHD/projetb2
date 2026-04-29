import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NetworkService } from '../../core/network.service';
import { OfflineQueueService } from '../../core/offline-queue.service';

@Component({
  selector: 'app-offline-banner',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (!network.isOnline()) {
      <div class="offline-banner" role="alert" aria-live="polite">
        <span>Mode hors-ligne</span>
        @if (network.lastDataAt()) {
          <span> — données du {{ network.lastDataAt() | date:'dd/MM à HH:mm' }}</span>
        }
        @if (queue.pendingCount() > 0) {
          <span class="offline-pending"> · {{ queue.pendingCount() }} action{{ queue.pendingCount() > 1 ? 's' : '' }} en attente</span>
        }
      </div>
    }
  `,
})
export class OfflineBannerComponent {
  network = inject(NetworkService);
  queue   = inject(OfflineQueueService);
}
