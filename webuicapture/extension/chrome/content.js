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


// Click event handler to trigger screenshot
document.addEventListener('click', () => {
    console.log("Sending capture message!", window.location.href);
    // chrome.runtime.sendMessage({ action: 'ping', message: "alive" })
    const pixelRatio = window.devicePixelRatio || 1;
    // do it in pixel space, this makes things easier later when processing the image
    const viewRect = [
        window.scrollX * pixelRatio,
        window.scrollY * pixelRatio,
        (window.scrollX + window.innerWidth) * pixelRatio,
        (window.scrollY + window.innerHeight) * pixelRatio
    ];
    chrome.runtime.sendMessage({
        action: 'capture',
        viewRect: viewRect, // this should be checked against the image size for sanity
        data: {
            url: window.location.href,
            timestamp: new Date().toISOString(),
            // TODO: traverse the dom and collect the bbox tree
            bbox_tree: extractLayoutTree(document.body, viewRect)
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
function extractLayoutTree(node, viewRect) {
    // TODO need to check that the view rect doesnt change as this is computed...

    const rect = node.getBoundingClientRect();
    if (rect.width == 0 || rect.height == 0) {
        // this element is not visible (probably...) so skip it.
        return null;
    }
    const pixelRatio = window.devicePixelRatio || 1;

    // TODO need to make sure the user doesnt scroll before the screen capture is taken!
    const _x1 = (rect.left + window.scrollX) * pixelRatio;
    const _y1 = (rect.top + window.scrollY) * pixelRatio;
    const _x2 = (rect.right + window.scrollX) * pixelRatio;
    const _y2 = (rect.bottom + window.scrollY) * pixelRatio;

    if (!rectangleIntersection([_x1, _y1, _x2, _y2], viewRect)) {
        // this element is not visible (probably...) so skip it.
        return null;
    }

    // clip the rectangle to the viewport
    const x1 = Math.floor(Math.max(_x1, viewRect[0]));
    const y1 = Math.floor(Math.max(_y1, viewRect[1]));
    const x2 = Math.floor(Math.min(_x2, viewRect[2]));
    const y2 = Math.floor(Math.min(_y2, viewRect[3]));

    console.log("viewRect", viewRect);
    console.log("Rect", [_x1, _y1, _x2, _y2]);
    console.log("Clipped", [x1, y1, x2, y2]);

    const info = {
        tag: node.tagName,
        bbox: [x1, y1, x2, y2],
        meta: {},
        children: []
    };

    Array.from(node.children).forEach(child => {
        const childInfo = extractLayoutTree(child, viewRect);
        if (childInfo) {
            info.children.push(childInfo);
        }
    });
    return info;
}
