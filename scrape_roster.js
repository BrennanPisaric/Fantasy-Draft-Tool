alert("Now click anywhere inside the 'Roster' panel on the LEFT side of the screen.");
document.addEventListener('click', function initRoster(e) {
    document.removeEventListener('click', initRoster);
    const rosterContainer = e.target.closest('div');
    alert("Attached to Roster! Syncing your team...");
    
    let seenRoster = new Set();
    setInterval(() => {
        const textNodes = document.createTreeWalker(rosterContainer, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while ((node = textNodes.nextNode())) {
            let text = node.textContent.trim();
            // Ignore "Empty" slots and position labels
            if (text.includes(' ') && text !== "Empty" && text.length > 4 && !seenRoster.has(text)) {
                seenRoster.add(text);
                fetch('http://localhost:8000', {
                    method: 'POST',
                    body: JSON.stringify({text: "MY_ROSTER:" + text})
                }).catch(e => {});
            }
        }
    }, 2000);
}, {capture: true, once: true});
