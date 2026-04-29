import { Component, OnInit, OnDestroy, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, interval, Subscription } from 'rxjs';

import { ApiService, Alert, Hive } from '../../core/api.service';
import { NetworkService } from '../../core/network.service';
import { OfflineQueueService } from '../../core/offline-queue.service';
import { NetworkBadgeComponent } from '../../shared/network-badge/network-badge.component';

interface DayGroup {
  day: string;
  dateKey: number;
  items: Alert[];
}

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule, NetworkBadgeComponent],
  templateUrl: './history.component.html',
})
export class HistoryComponent implements OnInit, OnDestroy {
  private api     = inject(ApiService);
  private network = inject(NetworkService);
  private queue   = inject(OfflineQueueService);
  private refreshSub?: Subscription;

  allGroups    = signal<DayGroup[]>([]);
  hiveNames    = signal<Record<number, string>>({});
  activeFilter = signal('all');
  hasNoAlerts  = signal(false);

  filteredGroups = computed(() => {
    const filter = this.activeFilter();
    const groups = this.allGroups();
    if (filter === 'all') return groups;

    if (filter === 'resolved') {
      return groups
        .map(g => ({ ...g, items: g.items.filter(i => i.is_resolved) }))
        .filter(g => g.items.length > 0);
    }

    return groups
      .map(g => ({ ...g, items: g.items.filter(i => i.severity === filter && !i.is_resolved) }))
      .filter(g => g.items.length > 0);
  });

  ngOnInit(): void {
    this.load();
    this.refreshSub = interval(30_000).subscribe(() => this.load());
  }

  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
  }

  private load(): void {
    forkJoin({
      active:   this.api.getAlerts(false),
      resolved: this.api.getAlerts(true),
      hives:    this.api.getHives(),
    }).subscribe({
      next: ({ active, resolved, hives }) => {
        this.network.markDataFresh();
        const names: Record<number, string> = {};
        hives.forEach(h => names[h.id] = h.name);
        this.hiveNames.set(names);

        const all = [...active, ...resolved].sort(
          (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );

        if (all.length === 0) {
          this.hasNoAlerts.set(true);
          return;
        }
        this.hasNoAlerts.set(false);
        this.allGroups.set(this.groupByDay(all));
      },
      error: err => console.error('Erreur chargement historique :', err),
    });
  }

  setFilter(filter: string): void {
    this.activeFilter.set(filter);
  }

  async resolveAlert(alert: Alert): Promise<void> {
    if (this.network.isOnline()) {
      this.api.resolveAlert(alert.id).subscribe({
        next: () => this.load(),
        error: (err) => console.error('Erreur résolution alerte :', err),
      });
    } else {
      await this.queue.enqueue({
        type: 'resolve_alert',
        payload: { alertId: alert.id },
        queuedAt: Date.now(),
      });
      // Mise à jour optimiste
      this.allGroups.set(
        this.allGroups().map((g) => ({
          ...g,
          items: g.items.map((i) => (i.id === alert.id ? { ...i, is_resolved: true } : i)),
        }))
      );
    }
  }

  hiveName(hiveId: number): string {
    return this.hiveNames()[hiveId] ?? `Ruche n°${hiveId}`;
  }

  private groupByDay(alerts: Alert[]): DayGroup[] {
    const groups: Record<string, { dateKey: number; items: Alert[] }> = {};
    for (const a of alerts) {
      const d = new Date(a.timestamp);
      const day = d.toLocaleDateString('fr-FR', {
        weekday: 'long', day: 'numeric', month: 'long',
      });
      if (!groups[day]) {
        groups[day] = { dateKey: d.setHours(0, 0, 0, 0), items: [] };
      }
      groups[day].items.push(a);
    }
    return Object.entries(groups)
      .map(([day, { dateKey, items }]) => ({ day, dateKey, items }))
      .sort((a, b) => b.dateKey - a.dateKey);
  }

  barClass(alert: Alert): string {
    if (alert.is_resolved) return 'ok';
    const map: Record<string, string> = { critical: 'alert', warning: 'warn', info: 'info' };
    return map[alert.severity] ?? 'ok';
  }

  severityLabel(alert: Alert): string {
    if (alert.is_resolved) return '✅ Résolu';
    const map: Record<string, string> = {
      critical: '🔴 Critique',
      warning:  '🟡 Avertissement',
      info:     '🔵 Info',
    };
    return map[alert.severity] ?? alert.severity;
  }

  formatTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }

  timeAgo(iso: string): string {
    const d    = new Date(iso);
    const diff = Date.now() - d.getTime();
    const min  = Math.floor(diff / 60_000);
    const time = this.formatTime(iso);

    if (min < 1)   return `À l'instant · ${time}`;
    if (min < 60)  return `Il y a ${min} min · ${time}`;
    const h = Math.floor(min / 60);
    if (h < 24)    return `Il y a ${h}h · ${time}`;
    if (h < 48)    return `Hier à ${time}`;
    return `${d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${time}`;
  }
}
