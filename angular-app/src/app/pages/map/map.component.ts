import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { ApiService, Hive } from '../../core/api.service';
import { NetworkService } from '../../core/network.service';
import { NetworkBadgeComponent } from '../../shared/network-badge/network-badge.component';

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule, TitleCasePipe, NetworkBadgeComponent],
  templateUrl: './map.component.html',
})
export class MapComponent implements OnInit {
  private api     = inject(ApiService);
  private network = inject(NetworkService);

  hives        = signal<Hive[]>([]);
  selectedHive = signal<Hive | null>(null);

  get alertCount(): number {
    return this.hives().filter(h => h.status !== 'normal').length;
  }

  ngOnInit(): void {
    this.api.getHives().subscribe({
      next: hives => { this.network.markDataFresh(); this.hives.set(hives); },
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
    return hive.status;
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