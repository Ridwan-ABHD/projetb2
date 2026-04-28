// chat.component.ts — Page Assistant IA
// Interface de chat avec le modèle Grok via notre backend Python (/chat/)

import { Component, OnInit, OnDestroy, signal, inject, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';

// Type d'un message dans le chat
interface Message {
  text: string;
  role: 'user' | 'bot';
  typing?: boolean; // true = indicateur "l'assistant réfléchit"
}

// Suggestions de questions prédéfinies (reproduit l'original)
const SUGGESTIONS = [
  { label: 'Ruche à surveiller ?',  q: 'Quelle ruche est la plus préoccupante en ce moment ?' },
  { label: 'Alertes actives',        q: 'Explique-moi les alertes actives.' },
  { label: 'État général',           q: "Donne-moi un résumé de l'état général du rucher." },
  { label: 'Que faire ?',            q: "Que faire si une ruche risque d'essaimer ?" },
];

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
})
export class ChatComponent implements OnInit, AfterViewChecked {
  private api = inject(ApiService);

  // Signal pour la liste de messages — chaque changement redessine le template
  messages = signal<Message[]>([]);

  // Propriété simple pour le champ de saisie (lié avec [(ngModel)])
  inputText = '';
  sending   = false; // Désactive le bouton pendant l'envoi

  suggestions = SUGGESTIONS;

  // Référence vers la zone de messages pour le scroll automatique
  // ViewChild : Angular trouve l'élément HTML avec #chatWrap dans le template
  @ViewChild('chatWrap') chatWrapRef?: ElementRef<HTMLDivElement>;

  ngOnInit(): void {
    // Message d'accueil de l'assistant
    this.messages.set([{
      text: "Bonjour ! Je suis votre assistant apicole IA. Posez-moi vos questions sur l'état de vos ruches.",
      role: 'bot',
    }]);
  }

  // Déclenché après chaque mise à jour du DOM — scrolle vers le bas
  ngAfterViewChecked(): void {
    if (this.chatWrapRef) {
      const el = this.chatWrapRef.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }

  // Envoie un message (depuis le formulaire ou depuis un bouton suggestion)
  sendMessage(text: string = this.inputText): void {
    if (!text.trim() || this.sending) return;

    this.inputText = ''; // Vide le champ de saisie
    this.sending   = true;

    // 1. Ajoute le message utilisateur dans la liste
    this.messages.update(msgs => [...msgs, { text, role: 'user' }]);

    // 2. Ajoute un indicateur "…" pendant que l'IA réfléchit
    this.messages.update(msgs => [...msgs, { text: '…', role: 'bot', typing: true }]);

    // 3. Appel API /chat/ — POST { message: text }
    this.api.chat(text).subscribe({
      next: data => {
        // Remplace le "…" par la vraie réponse (dernier élément de la liste)
        this.messages.update(msgs =>
          msgs.map((m, i) =>
            i === msgs.length - 1
              ? { text: data.response, role: 'bot' as const }
              : m
          )
        );
        this.sending = false;
      },
      error: () => {
        // En cas d'erreur, affiche un message d'erreur à la place du "…"
        this.messages.update(msgs =>
          msgs.map((m, i) =>
            i === msgs.length - 1
              ? { text: "Erreur : impossible de contacter l'assistant.", role: 'bot' as const }
              : m
          )
        );
        this.sending = false;
      },
    });
  }
}
