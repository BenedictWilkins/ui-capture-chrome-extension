const PORT = 7659;

function ping_server(message) {
    fetch(`http://localhost:${PORT}/ping`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
        .then(response => response.json())
        .then(data => console.log('Server response:', data))
        .catch(error => console.error('Error:', error));
}

function post_capture(data) {
    fetch(`http://localhost:${PORT}/upload`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => console.log('Server response:', data))
        .catch(error => console.error('Error:', error));
}

chrome.runtime.onInstalled.addListener(() => {
    console.log("UI-capture extension installed");
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'ping') {
        ping_server(request.message);
    } else if (request.action === 'capture') {
        chrome.tabs.captureVisibleTab(sender.tab.windowId, { format: 'png' }, (dataUrl) => {
            // TODO think about how to send the image more efficiently...? or stream it? or something... they might be quite large!
            // remove the prefix!
            request.data.image = dataUrl.split(',')[1];
            console.log(request.data);
            post_capture(request.data);
        });
    }
});

// TODO remove, just for testing...
function download_image(dataUrl) {
    chrome.downloads.download({
        url: dataUrl,
        filename: 'screenshot.png'
    }, (downloadId) => {
        if (chrome.runtime.lastError) {
            console.error("Download failed:", chrome.runtime.lastError);
        } else {
            console.log("Download started with ID:", downloadId);
        }
    });
}
