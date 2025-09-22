let selectedMode = null;
let lastModeChange = 'Not changed yet';
let modeChangeStatus = 'No changes made';
let modal;

export function initModeControls() {
    console.log('Initializing mode controls');
    
    // Initialize the modal
    const modalElement = document.getElementById('modeConfirmModal');
    if (modalElement) {
        modal = new bootstrap.Modal(modalElement);
    } else {
        console.error('Mode confirm modal not found in the DOM');
    }
    
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
    const confirmBtn = document.getElementById('confirm-mode-change');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            console.log('Confirming mode change to:', selectedMode);
            confirmModeChange();
        });
    }

    // Handle modal close/dismiss
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', function () {
            console.log('Modal closed, resetting state');
            selectedMode = null;
        });
    }

    // Debug
    console.log('Mode controls initialized');
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
        console.log('Mode change response:', data);
        
        // Handle different status responses
        if (data.status === 'confirm') {
            // Need confirmation - show modal
            const messageElement = document.getElementById('mode-change-message');
            if (messageElement) {
                messageElement.textContent = data.message || `Confirm changing to ${mode} mode?`;
            }
            if (modal) {
                modal.show();
            } else {
                console.error('Modal not initialized');
            }
        } else if (data.status === 'success') {
            // Mode changed successfully
            lastModeChange = new Date().toLocaleString();
            modeChangeStatus = 'Success: ' + data.message;
            updateModeDisplay(data.current_mode || mode);
            updateModeDebug();
            
            // Special handling for CHANGEOVER mode
            if (mode === 'CHANGEOVER') {
                handleModeChange(mode);
            }
        } else {
            // Error handling
            modeChangeStatus = 'Error: ' + (data.message || 'Unknown error');
            updateModeDebug();
        }
    })
    .catch(error => {
        console.error('Error in mode change request:', error);
        modeChangeStatus = 'Error: ' + error;
        updateModeDebug();
        selectedMode = null;
    });
}

function confirmModeChange() {
    if (!selectedMode) {
        console.error('No mode selected for confirmation');
        return;
    }

    console.log('Sending confirmation for mode:', selectedMode);
    
    fetch('/api/mode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            mode: selectedMode, 
            confirm: true 
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Mode change confirmation response:', data);
        
        if (modal) {
            modal.hide();
        }
        
        if (data.status === 'success') {
            lastModeChange = new Date().toLocaleString();
            modeChangeStatus = 'Success: ' + data.message;
            
            // Force an immediate state update
            fetch('/api/state')
                .then(response => response.json())
                .then(stateData => {
                    console.log('State after mode change:', stateData);
                    updateModeDisplay(stateData.current_mode || selectedMode);
                    
                    // Special handling for CHANGEOVER mode
                    if (selectedMode === 'CHANGEOVER') {
                        handleModeChange(selectedMode);
                    }
                })
                .catch(error => {
                    console.error('Error fetching state after mode change:', error);
                });
        } else {
            modeChangeStatus = 'Error: ' + (data.message || 'Unknown error');
            updateModeDebug();
        }
    })
    .catch(error => {
        console.error('Error in mode change confirmation:', error);
        modeChangeStatus = 'Error: ' + error;
        updateModeDebug();
        if (modal) {
            modal.hide();
        }
    })
    .finally(() => {
        selectedMode = null;
    });
}

export function updateModeDisplay(currentMode) {
    console.log('Updating mode display to:', currentMode);
    
    if (!currentMode) {
        console.warn('updateModeDisplay called with undefined or null mode');
        return;
    }
    
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
    const currentModeEl = document.getElementById('current-mode');
    const currentMode = currentModeEl ? currentModeEl.textContent : 'Unknown';
    
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

export function handleModeChange(newMode) {
    console.log('Handling mode change to:', newMode);
    
    if (newMode === 'CHANGEOVER') {
        // When entering changeover mode, start the distribution pump
        setTimeout(() => {
            console.log('Dispatching changeover-mode-entered event');
            const event = new CustomEvent('changeover-mode-entered');
            document.dispatchEvent(event);
        }, 500);  // Small delay to ensure UI is ready
    }
}

// Add this listener when the module loads
document.addEventListener('changeover-mode-entered', () => {
    console.log('Changeover mode entered event received - starting distribution pump');
    fetch('/api/distribution_pump', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            running: true 
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Distribution pump started:', data);
    })
    .catch(error => {
        console.error('Error starting distribution pump:', error);
    });
});
