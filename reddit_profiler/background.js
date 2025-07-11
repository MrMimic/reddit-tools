//
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Reddit Profiler] Message reçu:', request, sender);
  function setIconForTab(icon, tabId) {
    console.log('[Reddit Profiler] Changement d\'icône', icon, 'pour tabId', tabId);
    chrome.action.setIcon({
      path: {
        16: icon,
        48: icon,
        128: icon
      },
      tabId: tabId
    });
  }

  if (request.type === 'setIcon') {
    const tabId = sender.tab && sender.tab.id;
    if (tabId) {
      setIconForTab(request.icon, tabId);
    } else {
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) setIconForTab(request.icon, tabs[0].id);
      });
    }
    sendResponse({status: 'ok'});
  }
  if (request.type === 'checkCache') {
    // Par défaut, on met l'icône rouge
    const tabId = sender.tab && sender.tab.id;
    if (tabId) {
      setIconForTab('red-16.png', tabId);
    } else {
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) setIconForTab('red-16.png', tabs[0].id);
      });
    }
    // Puis on vérifie le cache
    fetch('http://localhost:5001/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: request.username })
    })
    .then(r => r.json())
    .then(response => {
      if (response.profile && response.profile.startsWith('[CACHE]')) {
        // Si profil en cache, on met l'icône verte
        if (tabId) {
          setIconForTab('green-16.png', tabId);
        } else {
          chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            if (tabs[0]) setIconForTab('green-16.png', tabs[0].id);
          });
        }
      }
    });
  }
});
