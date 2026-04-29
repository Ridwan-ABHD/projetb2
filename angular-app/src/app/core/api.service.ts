import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface LastReading {
  temperature: number;
  poids: number;
  frequence_moyenne: number | null;
  timestamp: string;
}

export interface Hive {
  id: string;
  name: string;
  last_reading: LastReading | null;
}

export interface Alert {
  id_mesure: number;
  id_ruche: string;
  timestamp: string;
  temperature: number;
  poids: number;
  frequence_moyenne: number | null;
  nom_alerte: string;
  description: string;
}

export interface AppSettings {
  id_regle: number;
  nom_alerte: string;
  freq_min: number;
  freq_max: number;
  temp_min: number;
  description: string;
}

export interface DiagnoseResult {
  hive_id: string;
  swarming_probability: number;
  dominant_frequency: number;
  stress_level: string;
  recommendation: string;
  analysis_duration: string;
}

export interface ChatResponse {
  response: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = 'http://localhost:8000';

  getHives(): Observable<Hive[]> {
    return this.http.get<Hive[]>(`${this.base}/hives/`);
  }

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(`${this.base}/alerts/`);
  }

  getSettings(): Observable<AppSettings[]> {
    return this.http.get<AppSettings[]>(`${this.base}/settings/`);
  }

  saveSettings(id_ruche: string, data: Partial<AppSettings>): Observable<AppSettings> {
    return this.http.put<AppSettings>(`${this.base}/settings/${id_ruche}`, data);
  }

  diagnose(hive_id: string, duration_seconds: number = 10): Observable<DiagnoseResult> {
    return this.http.post<DiagnoseResult>(`${this.base}/diagnose/`, { hive_id, duration_seconds });
  }

  chat(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.base}/chat/`, { message });
  }
}