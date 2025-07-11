// Content script : détecte la page profil et demande au background de changer l'icône
(function() {
  function updateIconForCurrentUrl() {
    const match = window.location.href.match(/reddit.com\/user\/([^\/]+)\/?$/);
    if (match) {
      const username = match[1];
      console.log('[Reddit Profiler] Profil détecté:', username);
      chrome.runtime.sendMessage({type: 'checkCache', username}, (resp) => {
        console.log('[Reddit Profiler] Message checkCache envoyé, réponse:', resp);
      });
    } else {
      chrome.runtime.sendMessage({type: 'setIcon', icon: 'red.png'}, (resp) => {
        console.log('[Reddit Profiler] Icône rouge (hors profil)', resp);
      });
    }
  }

  updateIconForCurrentUrl();

  let lastUrl = window.location.href;
  setInterval(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      updateIconForCurrentUrl();
    }
  }, 500);
})();
