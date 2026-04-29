import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService, AppSettings } from '../../core/api.service';
import { NetworkService } from '../../core/network.service';
import { OfflineQueueService } from '../../core/offline-queue.service';
import { NetworkBadgeComponent } from '../../shared/network-badge/network-badge.component';

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
  imports: [CommonModule, FormsModule, NetworkBadgeComponent],
  templateUrl: './settings.component.html',
})
export class SettingsComponent implements OnInit {
  private api     = inject(ApiService);
  private network = inject(NetworkService);
  readonly queue  = inject(OfflineQueueService);

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

  async ngOnInit(): Promise<void> {
    this.api.getSettings().subscribe({
      next: s => {
        this.freqWarning  = s.freq_warning;
        this.freqCritical = s.freq_critical;
        this.tempWarning  = s.temp_warning;
        this.humidityMax  = s.humidity_max;
      },
      error: err => console.error('Erreur chargement paramètres :', err),
    });

    // Chargement des toggles depuis IndexedDB (plus de localStorage)
    this.toggles.criticalAlerts = await this.queue.getPref('toggle_critical', true);
    this.toggles.silentMode     = await this.queue.getPref('toggle_silent', false);
  }

  async toggleCritical(): Promise<void> {
    this.toggles.criticalAlerts = !this.toggles.criticalAlerts;
    await this.queue.setPref('toggle_critical', this.toggles.criticalAlerts);
  }

  async toggleSilent(): Promise<void> {
    this.toggles.silentMode = !this.toggles.silentMode;
    await this.queue.setPref('toggle_silent', this.toggles.silentMode);
  }

  async save(): Promise<void> {
    const settings: AppSettings = {
      ...DEFAULTS,
      freq_warning:  this.freqWarning,
      freq_critical: this.freqCritical,
      temp_warning:  this.tempWarning,
      humidity_max:  this.humidityMax,
    };

    if (!this.network.isOnline()) {
      await this.queue.enqueue({ type: 'save_settings', payload: settings, queuedAt: Date.now() });
      this.showFeedback('Enregistré localement — sera synchronisé au retour du réseau', true);
      return;
    }

    this.api.saveSettings(settings).subscribe({
      next: () => this.showFeedback('Paramètres enregistrés ✓', true),
      error: () => this.showFeedback('Erreur lors de la sauvegarde', false),
    });
  }

  async reset(): Promise<void> {
    if (!this.network.isOnline()) {
      await this.queue.enqueue({ type: 'save_settings', payload: DEFAULTS, queuedAt: Date.now() });
      this.freqWarning  = DEFAULTS.freq_warning;
      this.freqCritical = DEFAULTS.freq_critical;
      this.tempWarning  = DEFAULTS.temp_warning;
      this.humidityMax  = DEFAULTS.humidity_max;
      this.toggles.criticalAlerts = true;
      this.toggles.silentMode     = false;
      await this.queue.setPref('toggle_critical', true);
      await this.queue.setPref('toggle_silent', false);
      this.showFeedback('Réinitialisé localement — sera synchronisé au retour du réseau', true);
      return;
    }

    this.api.saveSettings(DEFAULTS).subscribe({
      next: async () => {
        this.freqWarning  = DEFAULTS.freq_warning;
        this.freqCritical = DEFAULTS.freq_critical;
        this.tempWarning  = DEFAULTS.temp_warning;
        this.humidityMax  = DEFAULTS.humidity_max;
        this.toggles.criticalAlerts = true;
        this.toggles.silentMode     = false;
        await this.queue.setPref('toggle_critical', true);
        await this.queue.setPref('toggle_silent', false);
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
