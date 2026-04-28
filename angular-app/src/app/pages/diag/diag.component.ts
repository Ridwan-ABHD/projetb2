// diag.component.ts — Page Diagnostic IA
// Permet de lancer une analyse acoustique sur une ruche via l'API Grok
// et affiche le résultat avec probabilité d'essaimage, stress, recommandation

import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';   // Nécessaire pour [(ngModel)]
import { ActivatedRoute } from '@angular/router'; // Pour lire ?hive=3 dans l'URL

import { ApiService, Hive, DiagnoseResult } from '../../core/api.service';

@Component({
  selector: 'app-diag',
  standalone: true,
  imports: [
    CommonModule, // Pipes (number) + NgClass
    FormsModule,  // [(ngModel)] sur les inputs et selects
  ],
  templateUrl: './diag.component.html',
})
export class DiagComponent implements OnInit {
  private api   = inject(ApiService);
  private route = inject(ActivatedRoute); // Permet de lire les query params (?hive=3)

  // Données du formulaire — propriétés simples liées avec [(ngModel)]
  hives: Hive[] = [];
  selectedHiveId: number = 0; // ID de la ruche sélectionnée
  duration: number = 30;      // Durée d'écoute en secondes

  // État de l'analyse — signals pour le rendu réactif
  loading = signal(false);                    // true = analyse en cours
  result  = signal<DiagnoseResult | null>(null); // null = pas encore de résultat

  ngOnInit(): void {
    // 1. Charger la liste des ruches pour le <select>
    this.api.getHives().subscribe({
      next: hives => {
        this.hives = hives;

        // 2. Pré-sélectionner la ruche passée dans l'URL (?hive=3)
        // Équivalent de : new URLSearchParams(location.search).get("hive")
        const preselect = this.route.snapshot.queryParams['hive'];
        this.selectedHiveId = preselect
          ? parseInt(preselect, 10)
          : (hives[0]?.id ?? 0);
      },
      error: err => console.error('Erreur chargement ruches :', err),
    });
  }

  // Déclenche l'analyse IA
  diagnose(): void {
    if (!this.selectedHiveId) return;

    this.loading.set(true);  // Affiche le loader
    this.result.set(null);   // Cache l'ancien résultat

    this.api.diagnose(this.selectedHiveId, this.duration).subscribe({
      next: result => {
        this.result.set(result); // Affiche le résultat
        this.loading.set(false); // Cache le loader
      },
      error: err => {
        console.error('Erreur diagnostic :', err);
        this.loading.set(false);
      },
    });
  }

  // true si la probabilité d'essaimage dépasse 60% (affichage en orange)
  isHighProbability(): boolean {
    return (this.result()?.swarming_probability ?? 0) >= 60;
  }

  // true si le niveau de stress n'est pas normal
  isStressed(): boolean {
    return this.result()?.stress_level !== 'Normal';
  }
}
