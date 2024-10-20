// content.js

// // Create a pool of overlay elements
// const overlayPool = [];
// const maxOverlays = 100; // Adjust this number based on your needs
// overlayIndex = 0;

// // Initialize the overlay pool
// for (let i = 0; i < maxOverlays; i++) {
//     const overlay = document.createElement('div');
//     overlay.classList.add('overlay'); // overlay element style
//     document.body.appendChild(overlay);
//     overlayPool.push(overlay);
// }

// // Function to reset all overlays
// function resetOverlays() {
//     overlayIndex = 0;
//     for (const overlay of overlayPool) {
//         overlay.style.display = 'none';
//     }
// }
// // Function to highlight the element under the cursor
// function highlightElement(element, recursive = false) {
//     if (!element) return;
//     const overlay = overlayPool[overlayIndex];

//     const rect = element.getBoundingClientRect();
//     overlay.style.width = `${rect.width}px`;
//     overlay.style.height = `${rect.height}px`;
//     overlay.style.top = `${rect.top + window.scrollY}px`;
//     overlay.style.left = `${rect.left + window.scrollX}px`;
//     overlay.style.display = 'block';

//     if (recursive) {
//         // if (element.parentElement) {
//         //     overlayIndex = (overlayIndex + 1);
//         //     highlightElement(element.parentElement, recursive);
//         // }
//         Array.from(element.children).forEach(child => {
//             overlayIndex = (overlayIndex + 1)
//             highlightElement(child, recursive);
//         });
//     }
// }

// // Mousemove event handler, this will highlight the element under the cursor (for debugging purposes)
// document.addEventListener('mousemove', (event) => {
//     const element = document.elementFromPoint(event.clientX, event.clientY);
//     //console.log("Element:", element);
//     resetOverlays();
//     highlightElement(element, true);
// });


document.addEventListener('click', (event) => {
    if (!event.ctrlKey) {
        return;
    }
    console.log("Sending capture message!", window.location.href);
    // chrome.runtime.sendMessage({ action: 'ping', message: "alive" })
    //const pixelRatio = window.devicePixelRatio || 1;
    // do it in pixel space, this makes things easier later when processing the image
    chrome.runtime.sendMessage({
        action: 'capture',
        data: {
            url: window.location.href,
            timestamp: new Date().toISOString(),
            // TODO: traverse the dom and collect the bbox tree
            bbox_tree: extractLayoutTree(document.body)
        }
    });
});

function rectangleIntersection(rect1, rect2) {
    const [left1, top1, right1, bottom1] = rect1;
    const [left2, top2, right2, bottom2] = rect2;
    if (right1 < left2 || right2 < left1) {
        return false;
    }
    if (bottom1 < top2 || bottom2 < top1) {
        return false;
    }
    return true;
}

// TODO amazon fails (below) for some reason, the image size is not the same as the view port size...? 
// https://www.amazon.co.uk/gp/video/storefront/ref=atv_hm_hom_legacy_redirect?contentId=IncludedwithPrime&contentType=merch&merchId=IncludedwithPrime

// TODO slack also fails, it might be because we are using the document body as the root note...? 
// https://app.slack.com/client/T75FSCUT1/C07SMLPCESU

// make this a function
// Function to traverse the DOM and collect information about each element in a tree structure
function extractLayoutTree(node) {
    // TODO need to check that the view rect doesnt change as this is computed...
    if (!node.checkVisibility()) {
        // this element is not visible (probably...) so skip it and all its children
        return null;
    }
    const rect = node.getBoundingClientRect();
    const elemRect = [rect.left, rect.top, rect.right, rect.bottom];
    const viewRect = [0, 0, window.innerWidth, window.innerHeight];
    //console.log(node.checkVisibility(), elemRect, viewRect);


    if (!rectangleIntersection(elemRect, viewRect)) {
        // this element is not visible (probably...) so skip it.
        return null;
    }
    const pixelRatio = window.devicePixelRatio || 1;
    // clip the rectangle to the viewport
    const x1 = Math.floor(Math.max(elemRect[0], viewRect[0]) * pixelRatio);
    const y1 = Math.floor(Math.max(elemRect[1], viewRect[1]) * pixelRatio);
    const x2 = Math.floor(Math.min(elemRect[2], viewRect[2]) * pixelRatio);
    const y2 = Math.floor(Math.min(elemRect[3], viewRect[3]) * pixelRatio);

    const info = {
        tag: node.tagName,
        bbox: [x1, y1, x2, y2],
        meta: {},
        children: []
    };

    Array.from(node.children).forEach(child => {
        const childInfo = extractLayoutTree(child);
        if (childInfo) {
            info.children.push(childInfo);
        }
    });
    return info;
}
