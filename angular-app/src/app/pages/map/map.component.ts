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
    return this.hives().filter(h => {
      const freq = h.last_reading?.frequence_moyenne;
      return freq !== null && freq !== undefined && freq >= 260;
    }).length;
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

  hiveStatus(hive: Hive): string {
    const freq = hive.last_reading?.frequence_moyenne;
    if (freq === null || freq === undefined) return 'normal';
    if (freq >= 280) return 'critical';
    if (freq >= 260) return 'warning';
    return 'normal';
  }

  hiveColorClass(hive: Hive): string {
    const map: Record<string, string> = { normal: 'green', warning: 'orange', critical: 'red' };
    return map[this.hiveStatus(hive)] ?? 'green';
  }

  hiveBadgeClass(hive: Hive): string {
    const map: Record<string, string> = { normal: 'badge-green', warning: 'badge-orange', critical: 'badge-red' };
    return map[this.hiveStatus(hive)] ?? 'badge-green';
  }

  hiveStatusLabel(hive: Hive): string {
    const map: Record<string, string> = { normal: 'Normal', warning: 'Essaimage', critical: 'Alerte' };
    return map[this.hiveStatus(hive)] ?? 'Normal';
  }

  timeAgo(ts: string): string {
    const diff = Date.now() - new Date(ts).getTime();
    const min  = Math.floor(diff / 60_000);
    if (min < 1)  return "À l'instant";
    if (min < 60) return `Il y a ${min} min`;
    const h = Math.floor(min / 60);
    if (h < 24)   return `Il y a ${h}h`;
    return new Date(ts).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
  }
}