import { Injectable, inject } from '@angular/core';
import { environment } from '../../environments/environment';
import { ApiService } from './api.service';

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
}

@Injectable({ providedIn: 'root' })
export class PushService {
  private api = inject(ApiService);

  async init(): Promise<void> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

    try {
      const registration = await navigator.serviceWorker.ready;
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') return;

      const existing = await registration.pushManager.getSubscription();
      const subscription = existing ?? await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(environment.vapidPublicKey),
      });

      this.api.subscribePush(subscription.toJSON() as PushSubscriptionJSON).subscribe({
        error: (e) => console.warn('Push subscribe error', e),
      });
    } catch (err) {
      console.warn('Push init failed', err);
    }
  }
}
