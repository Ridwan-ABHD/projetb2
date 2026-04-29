// Configuration de production
// Les chemins API sont relatifs → nginx (Docker) redirige vers le backend
export const environment = {
  production: true,
  apiUrl: '',
  vapidPublicKey: 'BN1ky8SfmJhxKcrfNMwM5DjBU0EDk93MC1H1UJb5YloXYH1FSZOAVdWfynSl7kLAx52ZglSMbbyXdWDT4rH0P20',
};
