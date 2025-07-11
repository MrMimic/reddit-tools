// Content script : détecte la page profil et demande au background de changer l'icône
(function() {
  function updateIconForCurrentUrl() {
    const match = window.location.href.match(/reddit.com\/user\/([^\/]+)\/?$/);
    if (match) {
      const username = match[1];
      chrome.runtime.sendMessage({type: 'checkCache', username}, (resp) => {
        // L'icône sera verte si le profil est en cache (géré par le background)
        // Sinon elle reste rouge
        if (resp && resp.cached) {
          console.log('[Reddit Profiler] Profil en cache, icône verte');
        } else {
          console.log('[Reddit Profiler] Profil pas en cache, icône rouge');
        }
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
