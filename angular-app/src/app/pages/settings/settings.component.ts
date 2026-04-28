// settings.component.ts — Page Paramètres
// Permet de configurer les seuils d'alerte acoustiques et environnementaux

import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // Pour [(ngModel)] sur les inputs

import { ApiService, AppSettings } from '../../core/api.service';

// Valeurs par défaut (identiques à settings.js)
const DEFAULTS: AppSettings = {
  freq_warning:          260,
  freq_critical:         280,
  temp_warning:          36,
  temp_critical:         38,
  humidity_min:          50,
  humidity_max:          80,
  weight_drop_threshold: 2,
};

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
})
export class SettingsComponent implements OnInit {
  private api = inject(ApiService);

  // Valeurs des champs liées aux inputs via [(ngModel)]
  freqWarning  = DEFAULTS.freq_warning;
  freqCritical = DEFAULTS.freq_critical;
  tempWarning  = DEFAULTS.temp_warning;
  humidityMax  = DEFAULTS.humidity_max;

  // État des interrupteurs (toggles) — purement UI, non envoyés au backend
  toggles = {
    criticalAlerts: true,
    silentMode:     false,
  };

  // Feedback affiché après sauvegarde
  feedbackMsg = signal('');
  feedbackOk  = signal(true);

  ngOnInit(): void {
    // Chargement des paramètres actuels depuis le backend
    this.api.getSettings().subscribe({
      next: s => {
        this.freqWarning  = s.freq_warning;
        this.freqCritical = s.freq_critical;
        this.tempWarning  = s.temp_warning;
        this.humidityMax  = s.humidity_max;
      },
      error: err => console.error('Erreur chargement paramètres :', err),
    });
  }

  // Sauvegarde la configuration via PUT /settings/
  save(): void {
    const settings: AppSettings = {
      ...DEFAULTS,
      freq_warning:  this.freqWarning,
      freq_critical: this.freqCritical,
      temp_warning:  this.tempWarning,
      humidity_max:  this.humidityMax,
    };

    this.api.saveSettings(settings).subscribe({
      next: ()  => this.showFeedback('Paramètres enregistrés ✓', true),
      error: () => this.showFeedback('Erreur lors de la sauvegarde', false),
    });
  }

  // Réinitialise aux valeurs par défaut
  reset(): void {
    this.api.saveSettings(DEFAULTS).subscribe({
      next: () => {
        this.freqWarning  = DEFAULTS.freq_warning;
        this.freqCritical = DEFAULTS.freq_critical;
        this.tempWarning  = DEFAULTS.temp_warning;
        this.humidityMax  = DEFAULTS.humidity_max;
        this.showFeedback('Valeurs réinitialisées ✓', true);
      },
      error: () => this.showFeedback('Erreur lors de la réinitialisation', false),
    });
  }

  // Affiche un message de feedback pendant 2.5 secondes
  private showFeedback(msg: string, ok: boolean): void {
    this.feedbackMsg.set(msg);
    this.feedbackOk.set(ok);
    setTimeout(() => this.feedbackMsg.set(''), 2500);
  }
}
