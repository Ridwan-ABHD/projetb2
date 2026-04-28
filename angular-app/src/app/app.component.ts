// app.component.ts — Composant racine de l'application
// C'est le "squelette" qui contient toutes les autres pages via <router-outlet>

import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { BottomNavComponent } from './shared/bottom-nav/bottom-nav.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,        // Affiche la page correspondant à l'URL actuelle
    BottomNavComponent,  // Barre de navigation du bas (toujours visible)
  ],
  template: `
    <div class="app">
      <!-- La page courante s'affiche ici (Dashboard, Map, Diag...) -->
      <router-outlet></router-outlet>

      <!-- Barre de navigation fixe en bas -->
      <app-bottom-nav></app-bottom-nav>
    </div>
  `,
})
export class AppComponent {}
