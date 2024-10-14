// panel.js

document.getElementById('highlight-button').addEventListener('click', () => {
    const selector = prompt("Enter a CSS selector to highlight:");
    if (selector) {
        chrome.runtime.sendMessage({
            action: 'highlightElement',
            selector: selector
        });
    }
});

document.getElementById('clear-highlight-button').addEventListener('click', () => {
    chrome.runtime.sendMessage({
        action: 'clearHighlight'
    });
});
