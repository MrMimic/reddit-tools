document.getElementById('run-btn').addEventListener('click', async () => {
    document.getElementById('summary').value = 'Loading summary...';
    document.getElementById('answer').value = 'Loading answer...';
    const force = document.getElementById('force-checkbox').checked;
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
        const url = tabs[0].url;
        try {
            const resp = await fetch('http://localhost:5000/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, force })
            });
            const data = await resp.json();
            if (resp.ok) {
                document.getElementById('summary').value = data.summary || '';
                document.getElementById('answer').value = data.answer || '';
            } else {
                const errMsg = data.error || 'Unknown error';
                document.getElementById('summary').value = errMsg;
                document.getElementById('answer').value = errMsg;
            }
        } catch (e) {
            document.getElementById('summary').value = 'Network error: ' + e.message;
            document.getElementById('answer').value = 'Network error: ' + e.message;
        }
    });
});
