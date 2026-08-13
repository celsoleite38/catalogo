function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function ativarNotificacoes(slug) {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('Seu navegador não suporta notificações push.');
    return false;
  }

  const permissao = await Notification.requestPermission();
  if (permissao !== 'granted') {
    alert('Permissão de notificação negada.');
    return false;
  }

  const registration = await navigator.serviceWorker.ready;

  const keyResponse = await fetch(`/${slug}/push/vapid-public-key/`);
  const { publicKey } = await keyResponse.json();

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(publicKey),
  });

  await fetch(`/${slug}/push/subscribe/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(subscription),
  });

  localStorage.setItem(`push-ativado-${slug}`, '1');
  alert('Notificações ativadas!');
  return true;
}

async function desativarNotificacoes(slug) {
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();

  if (subscription) {
    await fetch(`/${slug}/push/unsubscribe/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ endpoint: subscription.endpoint }),
    });
    await subscription.unsubscribe();
  }

  localStorage.removeItem(`push-ativado-${slug}`);
}