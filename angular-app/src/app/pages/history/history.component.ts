// history.component.ts — Page Historique
// Affiche le journal des alertes groupées par jour avec filtrage par sévérité

import { Component, OnInit, OnDestroy, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, interval, Subscription } from 'rxjs';
import { switchMap, startWith } from 'rxjs/operators';

import { ApiService, Alert, Hive } from '../../core/api.service';

interface DayGroup {
  day: string;
  items: Alert[];
}

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './history.component.html',
})
export class HistoryComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private refreshSub?: Subscription;

  allGroups    = signal<DayGroup[]>([]);
  hiveNames    = signal<Record<number, string>>({});
  activeFilter = signal('all');
  hasNoAlerts  = signal(false);

  filteredGroups = computed(() => {
    const filter = this.activeFilter();
    const groups = this.allGroups();
    if (filter === 'all') return groups;

    const severityMap: Record<string, string> = {
      critical: 'critical',
      warning:  'warning',
      info:     'info',
      resolved: 'resolved',
    };
    const severity = severityMap[filter];

    if (severity === 'resolved') {
      return groups
        .map(g => ({ ...g, items: g.items.filter(i => i.is_resolved) }))
        .filter(g => g.items.length > 0);
    }

    return groups
      .map(g => ({ ...g, items: g.items.filter(i => i.severity === severity && !i.is_resolved) }))
      .filter(g => g.items.length > 0);
  });

  ngOnInit(): void {
    this.load();
    // Rafraîchissement automatique toutes les 30 secondes
    this.refreshSub = interval(30_000).subscribe(() => this.load());
  }

  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
  }

  private load(): void {
    forkJoin({
      alerts: this.api.getAlerts(),
      hives:  this.api.getHives(),
    }).subscribe({
      next: ({ alerts, hives }) => {
        const names: Record<number, string> = {};
        hives.forEach(h => names[h.id] = h.name);
        this.hiveNames.set(names);

        if (alerts.length === 0) {
          this.hasNoAlerts.set(true);
          return;
        }
        this.hasNoAlerts.set(false);
        this.allGroups.set(this.groupByDay(alerts));
      },
      error: err => console.error('Erreur chargement historique :', err),
    });
  }

  setFilter(filter: string): void {
    this.activeFilter.set(filter);
  }

  hiveName(hiveId: number): string {
    return this.hiveNames()[hiveId] ?? `Ruche n°${hiveId}`;
  }

  private groupByDay(alerts: Alert[]): DayGroup[] {
    const groups: Record<string, Alert[]> = {};
    for (const a of alerts) {
      const day = new Date(a.timestamp).toLocaleDateString('fr-FR', {
        weekday: 'long', day: 'numeric', month: 'long',
      });
      if (!groups[day]) groups[day] = [];
      groups[day].push(a);
    }
    return Object.entries(groups).map(([day, items]) => ({ day, items }));
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

  timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const min  = Math.floor(diff / 60_000);
    if (min < 1)  return "À l'instant";
    if (min < 60) return `Il y a ${min} min`;
    const h = Math.floor(min / 60);
    if (h < 24)   return `Il y a ${h}h`;
    return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' });
  }
}
