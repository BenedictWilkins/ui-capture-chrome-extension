// content.js

const overlay = document.createElement('div');
overlay.style.position = 'absolute';
overlay.style.backgroundColor = 'rgba(0, 128, 255, 0.3)';
overlay.style.border = '2px solid rgba(0, 128, 255, 0.8)';
overlay.style.zIndex = '9999';
overlay.style.pointerEvents = 'none';
overlay.style.display = 'none';
document.body.appendChild(overlay);

// Function to highlight the element under the cursor
function highlightElement(element) {
    if (!element) return;

    const rect = element.getBoundingClientRect();
    overlay.style.width = `${rect.width}px`;
    overlay.style.height = `${rect.height}px`;
    overlay.style.top = `${rect.top + window.scrollY}px`;
    overlay.style.left = `${rect.left + window.scrollX}px`;
    overlay.style.display = 'block';
}

// Mousemove event handler
document.addEventListener('mousemove', (event) => {
    const element = document.elementFromPoint(event.clientX, event.clientY);
    highlightElement(element);
});
