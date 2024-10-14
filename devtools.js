// devtools.js

chrome.devtools.panels.create(
    "UI Capture",
    "",
    "panel.html",
    function (panel) {
        panel.onShown.addListener((window) => {
            window.document.getElementById('highlight-button').onclick = () => {
                // Here you would specify the selector or target element
                const selector = prompt("Enter a CSS selector to highlight:");
                if (selector) {
                    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                        chrome.tabs.sendMessage(tabs[0].id, {
                            action: 'highlightElement',
                            selector: selector
                        });
                    });
                }
            };

            window.document.getElementById('clear-highlight-button').onclick = () => {
                chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                    chrome.tabs.sendMessage(tabs[0].id, {
                        action: 'clearHighlight'
                    });
                });
            };
        });
    }
);
