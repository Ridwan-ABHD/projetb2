import { Component, OnInit, OnDestroy, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { interval, Subscription } from 'rxjs';

import { ApiService, Alert } from '../../core/api.service';

interface DayGroup {
  day: string;
  dateKey: number;
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
  activeFilter = signal('all');
  hasNoAlerts  = signal(false);

  filteredGroups = computed(() => {
    const filter = this.activeFilter();
    const groups = this.allGroups();
    if (filter === 'all') return groups;
    return groups
      .map(g => ({ ...g, items: g.items.filter(i => i.id_ruche === filter) }))
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
    this.api.getAlerts().subscribe({
      next: (alerts) => {
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

  // ✅ Statut calculé depuis la fréquence
  barClass(alert: Alert): string {
    const freq = alert.frequence_moyenne;
    if (freq === null || freq === undefined) return 'info';
    if (freq >= 280) return 'alert';
    if (freq >= 260) return 'warn';
    return 'ok';
  }

  severityLabel(alert: Alert): string {
    const freq = alert.frequence_moyenne;
    if (freq === null || freq === undefined) return '🔵 Info';
    if (freq >= 280) return '🔴 Critique';
    if (freq >= 260) return '🟡 Avertissement';
    return '✅ Normal';
  }

  formatTime(ts: string): string {
    return new Date(ts).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }

  timeAgo(ts: string): string {
    const d    = new Date(ts);
    const diff = Date.now() - d.getTime();
    const min  = Math.floor(diff / 60_000);
    const time = this.formatTime(ts);
    if (min < 1)  return `À l'instant · ${time}`;
    if (min < 60) return `Il y a ${min} min · ${time}`;
    const h = Math.floor(min / 60);
    if (h < 24)   return `Il y a ${h}h · ${time}`;
    if (h < 48)   return `Hier à ${time}`;
    return `${d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })} à ${time}`;
  }
}