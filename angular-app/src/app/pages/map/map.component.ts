// map.component.ts — Page "Mes Ruches" (vue grille)
// Affiche toutes les ruches sous forme de cartes colorées selon leur statut

import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { ApiService, Hive } from '../../core/api.service';

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './map.component.html',
})
export class MapComponent implements OnInit {
  private api = inject(ApiService);

  hives = signal<Hive[]>([]); // Toutes les ruches

  // Compte les ruches qui ne sont pas en état "normal"
  get alertCount(): number {
    return this.hives().filter(h => h.status !== 'normal').length;
  }

  ngOnInit(): void {
    this.api.getHives().subscribe({
      next: hives => this.hives.set(hives),
      error: err  => console.error('Erreur chargement carte :', err),
    });
  }

  // Retourne la classe CSS de la carte de ruche (fond coloré)
  hiveColorClass(status: string): string {
    const map: Record<string, string> = {
      normal:   'green',
      warning:  'orange',
      critical: 'red',
    };
    return map[status] ?? 'green';
  }

  // Retourne la classe CSS du badge de statut
  hiveBadgeClass(status: string): string {
    const map: Record<string, string> = {
      normal:   'badge-green',
      warning:  'badge-orange',
      critical: 'badge-red',
    };
    return map[status] ?? 'badge-green';
  }

  // Retourne le libellé affiché dans le badge
  hiveStatusLabel(status: string): string {
    const map: Record<string, string> = {
      normal:   'Normal',
      warning:  'Essaimage',
      critical: 'Alerte',
    };
    return map[status] ?? 'Normal';
  }
}
