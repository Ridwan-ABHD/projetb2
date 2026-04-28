// Point d'entrée de l'application Angular
// C'est ici qu'on démarre tout et qu'on configure les services globaux

import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';

bootstrapApplication(AppComponent, {
  providers: [
    // Configure le routeur avec nos routes définies dans app.routes.ts
    provideRouter(routes),
    // Fournit HttpClient à toute l'application (nécessaire pour les appels API)
    provideHttpClient(),
  ],
}).catch(err => console.error(err));
