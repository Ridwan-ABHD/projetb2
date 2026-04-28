// map.component.ts — Page "Mes Ruches" (vue grille)
// Affiche toutes les ruches sous forme de cartes colorées selon leur statut
// Clic sur une carte → panneau de détail avec toutes les données capteurs

import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ApiService, Hive } from '../../core/api.service';

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map.component.html',
})
export class MapComponent implements OnInit {
  private api = inject(ApiService);

  hives        = signal<Hive[]>([]);
  selectedHive = signal<Hive | null>(null);

  get alertCount(): number {
    return this.hives().filter(h => h.status !== 'normal').length;
  }

  ngOnInit(): void {
    this.api.getHives().subscribe({
      next: hives => this.hives.set(hives),
      error: err  => console.error('Erreur chargement carte :', err),
    });
  }

  selectHive(hive: Hive): void {
    this.selectedHive.set(this.selectedHive()?.id === hive.id ? null : hive);
  }

  closeDetail(): void {
    this.selectedHive.set(null);
  }

  hiveColorClass(status: string): string {
    const map: Record<string, string> = { normal: 'green', warning: 'orange', critical: 'red' };
    return map[status] ?? 'green';
  }

  hiveBadgeClass(status: string): string {
    const map: Record<string, string> = { normal: 'badge-green', warning: 'badge-orange', critical: 'badge-red' };
    return map[status] ?? 'badge-green';
  }

  hiveStatusLabel(status: string): string {
    const map: Record<string, string> = { normal: 'Normal', warning: 'Essaimage', critical: 'Alerte' };
    return map[status] ?? 'Normal';
  }

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
