// app.routes.ts — Déclaration de toutes les routes de l'application
// Chaque route charge son composant de manière "lazy" (à la demande)
// pour que l'application démarre plus vite

import { Routes } from '@angular/router';

export const routes: Routes = [
  // Redirection de la racine vers le dashboard
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },

  // Page d'accueil — Tableau de bord général
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
  },

  // Page des ruches — Vue carte / grille
  {
    path: 'map',
    loadComponent: () =>
      import('./pages/map/map.component').then(m => m.MapComponent),
  },

  // Page historique — Journal des alertes
  {
    path: 'history',
    loadComponent: () =>
      import('./pages/history/history.component').then(m => m.HistoryComponent),
  },

  // Page paramètres — Seuils et configuration
  {
    path: 'settings',
    loadComponent: () =>
      import('./pages/settings/settings.component').then(m => m.SettingsComponent),
  },

  // Page assistant IA — Chat avec Grok
  {
    path: 'chat',
    loadComponent: () =>
      import('./pages/chat/chat.component').then(m => m.ChatComponent),
  },

  // Route de fallback — Redirige vers dashboard si URL inconnue
  { path: '**', redirectTo: 'dashboard' },
];
