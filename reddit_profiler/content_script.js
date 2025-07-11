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
      console.log('[Reddit Profiler] Pas une page profil Reddit, icône rouge');
      chrome.runtime.sendMessage({type: 'setIcon', icon: 'red-16.png'}, (resp) => {
        console.log('[Reddit Profiler] Message setIcon envoyé, réponse:', resp);
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
