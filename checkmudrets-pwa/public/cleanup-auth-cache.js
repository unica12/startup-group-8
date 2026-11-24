self.addEventListener('activate', (event) => {
  event.waitUntil(Promise.all(['api-receipts', 'api-stats'].map((name) => caches.delete(name))));
});
