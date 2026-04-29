// bottom-nav.component.ts — Barre de navigation du bas
// Partagée entre toutes les pages, affichée en permanence dans AppComponent

import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-bottom-nav',
  standalone: true,
  imports: [
    RouterLink,       // Permet [routerLink]="..." pour la navigation
    RouterLinkActive, // Ajoute la classe "active" sur le lien courant
  ],
  templateUrl: './bottom-nav.component.html',
})
export class BottomNavComponent {
  // Liste des onglets de navigation
  // Pour ajouter un onglet : ajouter un objet ici, le composant se met à jour automatiquement
  navItems = [
    { path: '/dashboard', label: 'Accueil',    icon: '/icons/nav/accueil.png'    },
    { path: '/map',       label: 'Ruches',     icon: '/icons/nav/ruche.png'      },
    { path: '/history',   label: 'Historique', icon: '/icons/nav/historique.png' },
    { path: '/settings',  label: 'Réglages',   icon: '/icons/nav/parametres.png' },
    { path: '/chat',      label: 'Assistant',  icon: '/icons/nav/bot.png'        },
  ];
}
