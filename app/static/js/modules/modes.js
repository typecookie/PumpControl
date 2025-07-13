let selectedMode = null;
let lastModeChange = 'Not changed yet';
let modeChangeStatus = 'No changes made';
let modal;

export function initModeControls() {
    // Initialize the modal
    modal = new bootstrap.Modal(document.getElementById('modeConfirmModal'));
    
    // Set up mode buttons click handlers
    document.querySelectorAll('.mode-button').forEach(button => {
        button.addEventListener('click', function() {
            const mode = this.getAttribute('data-mode');
            if (mode) {
                console.log('Mode button clicked:', mode);
                changeMode(mode);
            }
        });
    });

    // Set up mode change confirmation handler
    document.getElementById('confirm-mode-change').addEventListener('click', handleModeChangeConfirm);
}

export function updateModeDisplay(currentMode) {
    const currentModeElement = document.getElementById('current-mode');
    if (currentModeElement) {
        currentModeElement.textContent = currentMode;
    }
    
    // Update mode button highlighting
    document.querySelectorAll('.mode-button').forEach(button => {
        const buttonMode = button.getAttribute('data-mode');
        if (buttonMode === currentMode) {
            button.classList.add('active-mode');
        } else {
            button.classList.remove('active-mode');
        }
    });

    updateModeDebug();
    updateSectionVisibility(currentMode);
}

function updateModeDebug() {
    const currentMode = document.getElementById('current-mode').textContent || 'Unknown';
    const debugCurrentMode = document.getElementById('debug-current-mode');
    const debugLastModeChange = document.getElementById('debug-last-mode-change');
    const debugModeChangeStatus = document.getElementById('debug-mode-change-status');
    
    if (debugCurrentMode) debugCurrentMode.textContent = currentMode;
    if (debugLastModeChange) debugLastModeChange.textContent = lastModeChange;
    if (debugModeChangeStatus) debugModeChangeStatus.textContent = modeChangeStatus;
}

function updateSectionVisibility(mode) {
    const summerSection = document.getElementById('summer-tank-section');
    const winterSection = document.getElementById('winter-tank-section');
    const changeoverControls = document.getElementById('changeover-controls');

    if (summerSection) summerSection.style.display = mode === 'SUMMER' || mode === 'CHANGEOVER' ? 'block' : 'none';
    if (winterSection) winterSection.style.display = mode === 'WINTER' || mode === 'CHANGEOVER' ? 'block' : 'none';
    if (changeoverControls) changeoverControls.style.display = mode === 'CHANGEOVER' ? 'block' : 'none';
}

export function changeMode(mode) {
    console.log('changeMode called with mode:', mode);
    selectedMode = mode;
    
    fetch('/api/mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: mode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'confirmation_required') {
            const messageElement = document.getElementById('mode-change-message');
            if (messageElement) {
                messageElement.textContent = data.message;
            }
            modal.show();
        }
    })
    .catch(error => {
        console.error('Error in initial request:', error);
        modeChangeStatus = 'Error: ' + error;
        updateModeDebug();
    });
}

function handleModeChangeConfirm() {
    console.log('Mode change confirmed for mode:', selectedMode);
    
    fetch('/api/mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: selectedMode, confirm: true })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Confirmation response:', data);
        lastModeChange = new Date().toLocaleString();
        modeChangeStatus = 'Success: ' + data.message;
        updateModeDisplay(selectedMode);
        modal.hide();
    })
    .catch(error => {
        console.error('Error during confirmation:', error);
        modeChangeStatus = 'Error: ' + error;
        updateModeDebug();
        modal.hide();
    });
}