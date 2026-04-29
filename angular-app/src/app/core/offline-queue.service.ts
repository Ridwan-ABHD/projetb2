import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface QueuedAction {
  id?: number;
  type: 'resolve_alert' | 'save_settings';
  payload: unknown;
  queuedAt: number;
}

const DB_NAME = 'apicole-offline';
const DB_VERSION = 2;

@Injectable({ providedIn: 'root' })
export class OfflineQueueService {
  private http = inject(HttpClient);

  readonly pendingCount = signal(0);
  private readonly ready: Promise<IDBDatabase>;

  constructor() {
    this.ready = this.openDB();
    this.ready.then(() => this.refreshCount());
  }

  private openDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = (e) => {
        const db = (e.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('actions')) {
          db.createObjectStore('actions', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('prefs')) {
          db.createObjectStore('prefs', { keyPath: 'key' });
        }
      };
      req.onsuccess = (e) => resolve((e.target as IDBOpenDBRequest).result);
      req.onerror = (e) => reject((e.target as IDBOpenDBRequest).error);
    });
  }

  // ── Action queue ────────────────────────────────────────────────────────────

  async enqueue(action: Omit<QueuedAction, 'id'>): Promise<void> {
    const db = await this.ready;
    await this.idbOp(db, 'actions', 'add', action);
    await this.refreshCount();
  }

  async getAll(): Promise<QueuedAction[]> {
    const db = await this.ready;
    return this.idbGetAll<QueuedAction>(db, 'actions');
  }

  async dequeue(id: number): Promise<void> {
    const db = await this.ready;
    await this.idbOp(db, 'actions', 'delete', id);
    await this.refreshCount();
  }

  async flush(): Promise<void> {
    const actions = await this.getAll();
    for (const action of actions) {
      try {
        if (action.type === 'resolve_alert') {
          const { alertId } = action.payload as { alertId: number };
          await firstValueFrom(this.http.post(`/alerts/${alertId}/resolve`, {}));
        } else if (action.type === 'save_settings') {
          await firstValueFrom(this.http.put('/settings/', action.payload));
        }
        await this.dequeue(action.id!);
      } catch {
        break; // réseau toujours indisponible, on arrête le replay
      }
    }
  }

  // ── Prefs (remplace localStorage) ───────────────────────────────────────────

  async getPref<T>(key: string, defaultValue: T): Promise<T> {
    const db = await this.ready;
    return new Promise((resolve) => {
      const tx = db.transaction('prefs', 'readonly');
      const req = tx.objectStore('prefs').get(key);
      req.onsuccess = () => resolve(req.result ? (req.result.value as T) : defaultValue);
      req.onerror = () => resolve(defaultValue);
    });
  }

  async setPref<T>(key: string, value: T): Promise<void> {
    const db = await this.ready;
    await this.idbOp(db, 'prefs', 'put', { key, value });
  }

  // ── Helpers IDB ─────────────────────────────────────────────────────────────

  private idbOp(
    db: IDBDatabase,
    store: string,
    method: 'add' | 'put' | 'delete',
    data: unknown,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(store, 'readwrite');
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (tx.objectStore(store) as any)[method](data);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  private idbGetAll<T>(db: IDBDatabase, store: string): Promise<T[]> {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(store, 'readonly');
      const req = tx.objectStore(store).getAll();
      req.onsuccess = () => resolve(req.result as T[]);
      req.onerror = () => reject(req.error);
    });
  }

  private async refreshCount(): Promise<void> {
    const all = await this.getAll();
    this.pendingCount.set(all.length);
  }
}
