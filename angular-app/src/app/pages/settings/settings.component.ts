import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService, AppSettings } from '../../core/api.service';

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

  freqWarning  = DEFAULTS.freq_warning;
  freqCritical = DEFAULTS.freq_critical;
  tempWarning  = DEFAULTS.temp_warning;
  humidityMax  = DEFAULTS.humidity_max;

  toggles = {
    criticalAlerts: true,
    silentMode:     false,
  };

  feedbackMsg = signal('');
  feedbackOk  = signal(true);

  ngOnInit(): void {
    this.api.getSettings().subscribe({
      next: s => {
        this.freqWarning  = s.freq_warning;
        this.freqCritical = s.freq_critical;
        this.tempWarning  = s.temp_warning;
        this.humidityMax  = s.humidity_max;
      },
      error: err => console.error('Erreur chargement paramètres :', err),
    });

    // Chargement des toggles depuis localStorage
    const critical = localStorage.getItem('toggle_critical');
    const silent   = localStorage.getItem('toggle_silent');
    this.toggles.criticalAlerts = critical !== 'false';
    this.toggles.silentMode     = silent   === 'true';
  }

  toggleCritical(): void {
    this.toggles.criticalAlerts = !this.toggles.criticalAlerts;
    localStorage.setItem('toggle_critical', String(this.toggles.criticalAlerts));
  }

  toggleSilent(): void {
    this.toggles.silentMode = !this.toggles.silentMode;
    localStorage.setItem('toggle_silent', String(this.toggles.silentMode));
  }

  save(): void {
    const settings: AppSettings = {
      ...DEFAULTS,
      freq_warning:  this.freqWarning,
      freq_critical: this.freqCritical,
      temp_warning:  this.tempWarning,
      humidity_max:  this.humidityMax,
    };

    this.api.saveSettings(settings).subscribe({
      next: () => this.showFeedback('Paramètres enregistrés ✓', true),
      error: () => this.showFeedback('Erreur lors de la sauvegarde', false),
    });
  }

  reset(): void {
    this.api.saveSettings(DEFAULTS).subscribe({
      next: () => {
        this.freqWarning  = DEFAULTS.freq_warning;
        this.freqCritical = DEFAULTS.freq_critical;
        this.tempWarning  = DEFAULTS.temp_warning;
        this.humidityMax  = DEFAULTS.humidity_max;
        this.toggles.criticalAlerts = true;
        this.toggles.silentMode     = false;
        localStorage.setItem('toggle_critical', 'true');
        localStorage.setItem('toggle_silent', 'false');
        this.showFeedback('Valeurs réinitialisées ✓', true);
      },
      error: () => this.showFeedback('Erreur lors de la réinitialisation', false),
    });
  }

  private showFeedback(msg: string, ok: boolean): void {
    this.feedbackMsg.set(msg);
    this.feedbackOk.set(ok);
    setTimeout(() => this.feedbackMsg.set(''), 2500);
  }
}
