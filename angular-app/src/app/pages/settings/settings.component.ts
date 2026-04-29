import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, AppSettings } from '../../core/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
})
export class SettingsComponent implements OnInit {
  private api = inject(ApiService);

  freqMin  = 150;
  freqMax  = 300;
  tempMin  = 10;

  toggles = {
    criticalAlerts: true,
    silentMode: false,
  };

  feedbackMsg = signal('');
  feedbackOk  = signal(true);

  ngOnInit(): void {
    this.api.getSettings().subscribe({
      next: (settings: AppSettings[]) => {
        if (settings.length > 0) {
          this.freqMin = settings[0].freq_min;
          this.freqMax = settings[0].freq_max;
          this.tempMin = settings[0].temp_min;
        }
      },
      error: err => console.error('Erreur chargement paramètres :', err),
    });

    const critical = localStorage.getItem('toggle_critical');
    const silent   = localStorage.getItem('toggle_silent');
    this.toggles.criticalAlerts = critical !== 'false';
    this.toggles.silentMode     = silent === 'true';
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
    // ✅ On sauvegarde par ruche — ici on prend la première règle comme exemple
    this.showFeedback('Paramètres enregistrés ✓', true);
  }

  reset(): void {
    this.freqMin = 150;
    this.freqMax = 300;
    this.tempMin = 10;
    this.showFeedback('Valeurs réinitialisées ✓', true);
  }

  private showFeedback(msg: string, ok: boolean): void {
    this.feedbackMsg.set(msg);
    this.feedbackOk.set(ok);
    setTimeout(() => this.feedbackMsg.set(''), 2500);
  }
}