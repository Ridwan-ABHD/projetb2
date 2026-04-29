import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { ApiService, Hive, Alert } from '../../core/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  hives         = signal<Hive[]>([]);
  criticalAlert = signal<Alert | null>(null);

  avgFreq = signal(0);
  avgTemp = signal(0);

  ngOnInit(): void {
    forkJoin({
      hives:  this.api.getHives(),
      alerts: this.api.getAlerts(),
    }).subscribe({
      next: ({ hives, alerts }) => {
        this.hives.set(hives);

        // ✅ Plus de severity dans la nouvelle interface — on prend juste la première alerte
        this.criticalAlert.set(alerts.length > 0 ? alerts[0] : null);

        // ✅ Calcul des moyennes avec les vrais noms de colonnes
        const withReading = hives.filter(h => h.last_reading);
        if (withReading.length > 0) {
          this.avgTemp.set(
            withReading.reduce((sum, h) => sum + h.last_reading!.temperature, 0) / withReading.length
          );
          this.avgFreq.set(
            withReading
              .filter(h => h.last_reading!.frequence_moyenne !== null)
              .reduce((sum, h) => sum + (h.last_reading!.frequence_moyenne ?? 0), 0)
            / withReading.length
          );
        }
      },
      error: err => console.error('Erreur chargement dashboard :', err),
    });
  }

  // ✅ Statut calculé localement depuis la fréquence
  statusDot(hive: Hive): string {
    const freq = hive.last_reading?.frequence_moyenne;
    if (freq === null || freq === undefined) return 'dot-green';
    if (freq >= 280) return 'dot-red';
    if (freq >= 260) return 'dot-orange';
    return 'dot-green';
  }

  statusLabel(hive: Hive): string {
    const freq = hive.last_reading?.frequence_moyenne;
    if (freq === null || freq === undefined) return 'État normal';
    if (freq >= 280) return "Alerte critique";
    if (freq >= 260) return "Risque d'essaimage";
    return 'État normal';
  }
}