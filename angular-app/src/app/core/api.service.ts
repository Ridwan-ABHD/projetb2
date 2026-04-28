// api.service.ts — Service HTTP centralisé
// Toutes les communications avec le backend Python passent par ici

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Alert {
  id: number;
  hive_id: number;
  severity: 'critical' | 'warning' | 'info';
  type: string;
  message: string;
  timestamp: string;
  is_resolved: boolean;
}

export interface Hive {
  id: number;
  name: string;
  location: string;
  status: 'normal' | 'warning' | 'critical';
  last_reading: {
    id: number;
    frequency_hz: number;
    temperature_c: number;
    humidity_pct: number;
    weight_kg: number;
    timestamp: string;
  } | null;
  active_alerts: Alert[];
}

export interface DiagnoseResult {
  hive_name: string;
  swarming_probability: number;
  dominant_frequency: number;
  stress_level: string;
  duration_seconds: number;
  recommendation: string;
}

export interface AppSettings {
  freq_warning: number;
  freq_critical: number;
  temp_warning: number;
  temp_critical: number;
  humidity_min: number;
  humidity_max: number;
  weight_drop_threshold: number;
}

export interface ChatResponse {
  response: string;
}

// Base vide = chemins relatifs → nginx proxy vers backend en prod Docker
@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = '';

  getHives(): Observable<Hive[]> {
    return this.http.get<Hive[]>(`${this.base}/hives/`);
  }

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(`${this.base}/alerts/`);
  }

  getSettings(): Observable<AppSettings> {
    return this.http.get<AppSettings>(`${this.base}/settings/`);
  }

  saveSettings(settings: AppSettings): Observable<AppSettings> {
    return this.http.put<AppSettings>(`${this.base}/settings/`, settings);
  }

  chat(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.base}/chat/`, { message });
  }
}
