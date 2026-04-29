import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NetworkService } from '../../core/network.service';
import { OfflineQueueService } from '../../core/offline-queue.service';

@Component({
  selector: 'app-network-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="net-badge" [class.net-badge--offline]="!network.isOnline()">
      <span class="net-dot"></span>
      <span>{{ network.isOnline() ? 'En ligne' : 'Hors-ligne' }}</span>
      @if (queue.pendingCount() > 0) {
        <span class="net-pending" [title]="queue.pendingCount() + ' action(s) en attente de sync'">
          {{ queue.pendingCount() }}
        </span>
      }
    </div>
  `,
})
export class NetworkBadgeComponent {
  network = inject(NetworkService);
  queue   = inject(OfflineQueueService);
}
