document.getElementById('profileBtn').addEventListener('click', async () => {
  document.getElementById('loading').style.display = 'block';
  document.getElementById('profile').textContent = '';
  const force = document.getElementById('force-checkbox').checked;
  chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
    const tab = tabs[0];
    chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: () => {
        const match = window.location.href.match(/reddit.com\/user\/([^\/]+)\/?$/);
        return match ? match[1] : null;
      },
    }, async (results) => {
      const username = results[0].result;
      if (!username) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('profile').textContent = 'Va sur un profil Reddit, banane !';
        chrome.runtime.sendMessage({type: 'setIcon', icon: 'red.png'});
        return;
      }
      const response = await fetch('http://localhost:5001/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, force })
      }).then(r => r.json());
      document.getElementById('loading').style.display = 'none';
      document.getElementById('profile').textContent = response.profile || response.error || 'Erreur API.';
      // Change icon selon cache
      if (response.profile && response.profile.startsWith('[CACHE]')) {
        chrome.runtime.sendMessage({type: 'setIcon', icon: 'green.png'});
      } else {
        chrome.runtime.sendMessage({type: 'setIcon', icon: 'red.png'});
      }
    });
  });
});
