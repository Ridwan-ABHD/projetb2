// dashboard.component.ts — Page d'accueil (tableau de bord)
// Affiche les KPIs en direct, les alertes critiques et la liste des ruches

import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService, Hive, Alert } from '../../core/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, // Fournit les pipes (number, date) et NgClass
    RouterLink,   // Permet les liens [routerLink]
  ],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  // inject() récupère le service — Angular 18 recommande cette syntaxe
  private api = inject(ApiService);

  // --- État de la page (Signals = variables réactives) ---
  // Quand on appelle .set(), Angular met à jour le template automatiquement

  hives = signal<Hive[]>([]);           // Liste de toutes les ruches
  criticalAlert = signal<Alert | null>(null); // Première alerte critique (pour la bannière)

  // Moyennes des capteurs (KPIs)
  avgFreq     = signal(0); // Fréquence acoustique moyenne (Hz)
  avgTemp     = signal(0); // Température moyenne (°C)
  avgHumidity = signal(0); // Humidité moyenne (%)

  ngOnInit(): void {
    // forkJoin : Lance les 2 requêtes en parallèle et attend que les 2 soient terminées
    // C'est l'équivalent Angular de Promise.all()
    forkJoin({
      hives:  this.api.getHives(),
      alerts: this.api.getAlerts(),
    }).subscribe({
      next: ({ hives, alerts }) => {
        this.hives.set(hives);

        // On cherche la première alerte "critique" pour l'afficher en bannière rouge
        const critical = alerts.find(a => a.severity === 'critical') ?? null;
        this.criticalAlert.set(critical);

        // Calcul des moyennes uniquement sur les ruches qui ont une lecture capteur
        const withReading = hives.filter(h => h.last_reading);
        if (withReading.length > 0) {
          const avg = (key: 'frequency_hz' | 'temperature_c' | 'humidity_pct') =>
            withReading.reduce((sum, h) => sum + h.last_reading![key], 0) / withReading.length;

          this.avgFreq.set(avg('frequency_hz'));
          this.avgTemp.set(avg('temperature_c'));
          this.avgHumidity.set(avg('humidity_pct'));
        }
      },
      error: err => console.error('Erreur chargement dashboard :', err),
    });
  }

  // Retourne la classe CSS du point de couleur selon le statut de la ruche
  statusDot(status: string): string {
    const map: Record<string, string> = {
      normal:   'dot-green',
      warning:  'dot-orange',
      critical: 'dot-red',
    };
    return map[status] ?? 'dot-green';
  }

  // Retourne le texte lisible du statut
  statusLabel(status: string): string {
    const map: Record<string, string> = {
      normal:   'État normal',
      warning:  "Risque d'essaimage",
      critical: 'Alerte critique',
    };
    return map[status] ?? '';
  }
}
