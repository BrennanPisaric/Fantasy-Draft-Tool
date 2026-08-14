alert("Please click anywhere inside the 'Picks' panel on the right side of the screen.");
document.addEventListener('click', function initObserver(e) {
    document.removeEventListener('click', initObserver);
    const picksContainer = e.target.closest('div'); // Grab the clicked container
    alert("Attached to panel! Syncing picks to local app...");
    
    let seenText = new Set();
    setInterval(() => {
        // Get all text nodes in the panel
        const textNodes = document.createTreeWalker(picksContainer, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while ((node = textNodes.nextNode())) {
            let text = node.textContent.trim();
            if (text.includes(' ') && text.length > 4 && !seenText.has(text)) {
                seenText.add(text);
                fetch('http://localhost:8000', {
                    method: 'POST',
                    body: JSON.stringify({text: text})
                }).catch(e => {}); // Ignore network errors
            }
        }
    }, 2000);
}, {capture: true, once: true});
