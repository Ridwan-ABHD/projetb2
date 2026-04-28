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
  id: number;
  name: string;
  location: string;
  status: 'normal' | 'warning' | 'critical';
  last_reading: {
    frequency_hz: number;
    temperature_c: number;
    humidity_pct: number;
  } | null;
}

export interface Alert {
  id: number;
  hive_id: number;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string; // Format ISO 8601 ex: "2024-04-28T14:30:00"
}

export interface DiagnoseResult {
  hive_name: string;
  swarming_probability: number; // 0 à 100 (%)
  dominant_frequency: number;   // en Hz
  stress_level: string;         // ex: "Normal", "Élevé"
  duration_seconds: number;
  recommendation: string;
}

export interface AppSettings {
  freq_warning: number;          // Seuil alerte essaimage (Hz)
  freq_critical: number;         // Seuil alerte maladie (Hz)
  temp_warning: number;          // Température max (°C)
  temp_critical: number;
  humidity_min: number;
  humidity_max: number;
  weight_drop_threshold: number;
}

export interface ChatResponse {
  response: string;
}

// ============================================================
// Service Injectable — Angular le crée une seule fois (singleton)
// ============================================================

@Injectable({ providedIn: 'root' })
export class ApiService {
  // inject() est la façon moderne Angular 18 d'obtenir un service
  // C'est équivalent à écrire constructor(private http: HttpClient) {}
  private http = inject(HttpClient);

  // Base URL vide = chemins relatifs
  // En développement : le proxy redirige vers localhost:8000
  // En production (Docker) : nginx redirige vers le backend
  private base = '';

  // --- Récupère toutes les ruches avec leur dernière lecture capteur ---
  getHives(): Observable<Hive[]> {
    return this.http.get<Hive[]>(`${this.base}/hives/`);
  }

  // --- Récupère toutes les alertes (triées par date desc côté API) ---
  getAlerts(): Observable<Alert[]> {
    return this.http.get<Alert[]>(`${this.base}/alerts/`);
  }

  // --- Lance une analyse acoustique IA sur une ruche ---
  diagnose(hiveId: number, durationSeconds: number): Observable<DiagnoseResult> {
    return this.http.post<DiagnoseResult>(`${this.base}/diagnose/`, {
      hive_id: hiveId,
      duration_seconds: durationSeconds,
    });
  }

  // --- Récupère la configuration des seuils ---
  getSettings(): Observable<AppSettings> {
    return this.http.get<AppSettings>(`${this.base}/settings/`);
  }

  // --- Sauvegarde la configuration des seuils ---
  saveSettings(settings: AppSettings): Observable<AppSettings> {
    return this.http.put<AppSettings>(`${this.base}/settings/`, settings);
  }

  // --- Envoie un message au chatbot Grok ---
  chat(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.base}/chat/`, { message });
  }
}
