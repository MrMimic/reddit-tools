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
    const tabId = sender.tab && sender.tab.id;
    // Par défaut, icône rouge
    if (tabId) {
      setIconForTab('red.png', tabId);
    } else {
      chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) setIconForTab('red.png', tabs[0].id);
      });
    }
    // Vérifie juste le cache, ne génère jamais le profil
    fetch('http://localhost:5001/profile/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: request.username })
    })
    .then(r => r.json())
    .then(response => {
      if (response.cached) {
        // Profil en cache, icône verte
        if (tabId) {
          setIconForTab('green.png', tabId);
        } else {
          chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            if (tabs[0]) setIconForTab('green.png', tabs[0].id);
          });
        }
      }
      sendResponse({cached: response.cached});
    });
    return true;
  }
});
