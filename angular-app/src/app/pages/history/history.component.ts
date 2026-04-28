// history.component.ts — Page Historique
// Affiche le journal des alertes groupées par jour avec filtrage par type

import { Component, OnInit, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ApiService, Alert } from '../../core/api.service';

// Type interne pour grouper les alertes par jour
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
export class HistoryComponent implements OnInit {
  private api = inject(ApiService);

  allGroups    = signal<DayGroup[]>([]); // Toutes les alertes groupées par jour
  activeFilter = signal('all');          // Filtre actif : 'all' | 'critical' | 'warning' | 'info'
  hasNoAlerts  = signal(false);

  // computed() recalcule automatiquement quand allGroups ou activeFilter change
  filteredGroups = computed(() => {
    const filter = this.activeFilter();
    const groups = this.allGroups();

    if (filter === 'all') return groups;

    // Correspondance chip → severity API
    const severityMap: Record<string, string> = {
      alerts:      'critical',
      diagnostics: 'warning',
      sensors:     'info',
    };
    const severity = severityMap[filter];

    return groups
      .map(g => ({ ...g, items: g.items.filter(i => i.severity === severity) }))
      .filter(g => g.items.length > 0);
  });

  ngOnInit(): void {
    this.api.getAlerts().subscribe({
      next: alerts => {
        if (alerts.length === 0) {
          this.hasNoAlerts.set(true);
          return;
        }
        this.allGroups.set(this.groupByDay(alerts));
      },
      error: err => console.error('Erreur chargement historique :', err),
    });
  }

  // Change le filtre actif (appelé au clic sur un chip)
  setFilter(filter: string): void {
    this.activeFilter.set(filter);
  }

  // Regroupe un tableau d'alertes par date (format "lundi 28 avril")
  private groupByDay(alerts: Alert[]): DayGroup[] {
    const groups: Record<string, Alert[]> = {};
    for (const a of alerts) {
      const day = new Date(a.timestamp).toLocaleDateString('fr-FR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      });
      if (!groups[day]) groups[day] = [];
      groups[day].push(a);
    }
    return Object.entries(groups).map(([day, items]) => ({ day, items }));
  }

  // Classe CSS de la barre de couleur latérale selon la sévérité
  barClass(severity: string): string {
    const map: Record<string, string> = {
      critical: 'alert',
      warning:  'warn',
      info:     'info',
    };
    return map[severity] ?? 'ok';
  }

  // Texte lisible de la sévérité
  severityLabel(severity: string): string {
    const map: Record<string, string> = {
      critical: 'Alerte critique',
      warning:  'Avertissement',
      info:     'Info',
    };
    return map[severity] ?? severity;
  }

  // Calcule le temps écoulé depuis une date ISO (ex: "Il y a 3h")
  timeAgo(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const min  = Math.floor(diff / 60_000);
    if (min < 1)  return "À l'instant";
    if (min < 60) return `Il y a ${min} min`;
    const h = Math.floor(min / 60);
    if (h < 24)   return `Il y a ${h}h`;
    return new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
  }
}
