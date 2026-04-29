// app.component.ts — Composant racine de l'application
// C'est le "squelette" qui contient toutes les autres pages via <router-outlet>

import { Component, inject, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { BottomNavComponent } from './shared/bottom-nav/bottom-nav.component';
import { OfflineBannerComponent } from './shared/offline-banner/offline-banner.component';
import { PushService } from './core/push.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    BottomNavComponent,
    OfflineBannerComponent,
  ],
  template: `
    <div class="app">
      <app-offline-banner></app-offline-banner>
      <router-outlet></router-outlet>
      <app-bottom-nav></app-bottom-nav>
    </div>
  `,
})
export class AppComponent implements OnInit {
  private push = inject(PushService);

  ngOnInit(): void {
    this.push.init();
  }
}
