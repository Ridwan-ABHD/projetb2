// api.service.ts — Service HTTP centralisé
// Remplace les fonctions get(), post(), put() de l'ancien api.js
// Toutes les communications avec le backend Python passent par ici

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// ============================================================
// Interfaces TypeScript — Elles décrivent la forme des données
// retournées par notre API Python (miroir des modèles Pydantic)
// ============================================================

export interface Hive {
  id_ruche: string;        // Anciennement 'id' ou 'name'
  temperature: number;      // Anciennement 'temperature_c'
  poids: number;            // Anciennement 'weight_kg'
  frequence_moyenne?: number; // Correspond à 'frequency_hz'
  timestamp?: string;
}

export interface Alert {
  nom_regle: string;        // Le type d'alerte (Essaimage, etc.)
  id_ruche: string;
}

export interface AppSettings {
  freq_warning: number;
  freq_critical: number;
  temp_warning: number;
  temp_critical: number;
}
// Garde le reste du service avec ces noms

export interface DiagnoseResult {
  hive_id: string;
  swarming_probability: number;
  dominant_frequency: number;
  stress_level: string;
  recommendation: string;
}
export interface ChatResponse {
  response: string;
}

// ============================================================
// Service Injectable — Angular le crée une seule fois (singleton)
// ============================================================

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = 'http://127.0.0.1:8000'; // Port par défaut de FastAPI

  getHives(): Observable<Hive[]> {
    return this.http.get<Hive[]>(`${this.base}/hives/`);
  }

  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(`${this.base}/alerts/`);
  }

  // Utilise string pour hiveId car c'est "CF003"
  diagnose(hiveId: string, durationSeconds: number): Observable<DiagnoseResult> {
    return this.http.post<DiagnoseResult>(`${this.base}/diagnose/`, {
      hive_id: hiveId,
      duration_seconds: durationSeconds,
    });
  }

  chat(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.base}/chat/`, { message });
  }
}