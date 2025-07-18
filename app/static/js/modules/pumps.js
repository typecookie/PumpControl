let wellPumpRunning = false;
let distPumpRunning = true;  // Default to ON for distribution pump
let wellPumpReverse = false;

export function initPumpControls() {
    const wellPumpToggle = document.getElementById('manual-well-pump-toggle');
    const distPumpToggle = document.getElementById('manual-dist-pump-toggle');
    const reverseToggle = document.getElementById('well-pump-reverse-toggle');
    
    if (wellPumpToggle) {
        wellPumpToggle.addEventListener('click', () => handlePumpToggle('well'));
    }
    
    if (distPumpToggle) {
        distPumpToggle.addEventListener('click', () => handlePumpToggle('dist'));
    }

    // Add reverse toggle handler
    if (reverseToggle) {
        reverseToggle.addEventListener('change', function() {
            const enabled = this.checked;
            fetch('/api/well-pump-reverse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled: enabled })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    wellPumpReverse = enabled;
                    updatePumpButtonStates();
                } else {
                    console.error('Failed to set reverse mode:', data.message);
                    reverseToggle.checked = !enabled;
                }
            })
            .catch(error => {
                console.error('Error setting reverse mode:', error);
                reverseToggle.checked = !enabled;
            });
        });
    }

    // Initial update of pump displays
    updatePumpDisplays({
        well_pump_status: 'OFF',
        dist_pump_status: 'ON',
        current_mode: 'CHANGEOVER'
    });
}

export function updatePumpDisplays(data) {
    // Update reverse mode state if provided
    if (typeof data.well_pump_reverse !== 'undefined') {
        wellPumpReverse = data.well_pump_reverse;
        const reverseToggle = document.getElementById('well-pump-reverse-toggle');
        if (reverseToggle) {
            reverseToggle.checked = wellPumpReverse;
        }
    }

    // Update pump status displays
    const wellStatus = data.well_pump_status;
    const distStatus = data.dist_pump_status;
    
    document.getElementById('well-pump-status').textContent = wellStatus;
    document.getElementById('dist-pump-status').textContent = distStatus;

    // Update pump images
    updatePumpImage('well-pump', wellStatus);
    updatePumpImage('dist-pump', distStatus);

    // Only show manual controls in CHANGEOVER mode
    const changeoverControls = document.getElementById('changeover-controls');
    if (changeoverControls) {
        changeoverControls.style.display = data.current_mode === 'CHANGEOVER' ? 'block' : 'none';
        
        if (data.current_mode === 'CHANGEOVER') {
            updateManualPumpControl('well', wellStatus);
            updateManualPumpControl('dist', distStatus);
        }
    }

    // Update running states
    wellPumpRunning = wellStatus === 'ON';
    distPumpRunning = distStatus === 'ON';
}

function updatePumpImage(pumpId, status) {
    const imageElement = document.getElementById(`${pumpId}-image`);
    if (imageElement) {
        const imagePath = status === 'ON'
            ? '/static/img/pump_on.jpg'
            : '/static/img/pump_off.jpg';
        imageElement.src = imagePath;
    }

    const statusElement = document.getElementById(`${pumpId}-status`);
    if (statusElement) {
        statusElement.className = status === 'ON' ? 'pump-status status-on' : 'pump-status status-off';
    }
}

function updateManualPumpControl(pumpType, pumpStatus) {
    const isWell = pumpType === 'well';
    const buttonId = `manual-${pumpType}-pump-toggle`;
    const statusId = `manual-${pumpType}-pump-status`;
    let pumpRunning = pumpStatus === 'ON';
    
    // If it's the well pump and reverse mode is on, invert the display state
    if (isWell && wellPumpReverse) {
        pumpRunning = !pumpRunning;
    }
    
    const pumpButton = document.getElementById(buttonId);
    if (pumpButton) {
        pumpButton.textContent = pumpRunning ? `Stop ${isWell ? 'Well' : 'Distribution'} Pump` : `Start ${isWell ? 'Well' : 'Distribution'} Pump`;
        pumpButton.className = `btn pump-control-button ${pumpRunning ? 'btn-danger' : 'btn-primary'}`;
    }
    
    const statusElement = document.getElementById(statusId);
    if (statusElement) {
        statusElement.textContent = pumpRunning ? 'ON' : 'OFF';
    }
    
    if (isWell) {
        wellPumpRunning = pumpRunning;
    } else {
        distPumpRunning = pumpRunning;
    }
}

function handlePumpToggle(pumpType) {
    const isWell = pumpType === 'well';
    const currentState = isWell ? wellPumpRunning : distPumpRunning;
    let newState = !currentState;
    
    // If it's the well pump and reverse mode is on, invert the state we send to the server
    if (isWell && wellPumpReverse) {
        newState = !newState;
    }
    
    const endpoint = isWell ? '/api/pump' : '/api/distribution_pump';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ running: newState })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            if (isWell) {
                wellPumpRunning = wellPumpReverse ? !newState : newState;
            } else {
                distPumpRunning = newState;
            }
            
            // Update the UI
            const status = data.pump_running ? 'ON' : 'OFF';
            updateManualPumpControl(pumpType, status);
            document.getElementById(`${pumpType}-pump-status`).textContent = status;
            
            // Update pump image
            updatePumpImage(`${pumpType}-pump`, status);
        } else {
            console.error('Failed to toggle pump:', data.message);
        }
    })
    .catch(error => {
        console.error('Error toggling pump:', error);
    });
}

function updatePumpButtonStates() {
    const wellPumpButton = document.getElementById('manual-well-pump-toggle');
    const wellPumpStatus = document.getElementById('manual-well-pump-status');
    
    if (wellPumpButton && wellPumpStatus) {
        const displayState = wellPumpReverse ? !wellPumpRunning : wellPumpRunning;
        wellPumpButton.textContent = displayState ? 'Stop Well Pump' : 'Start Well Pump';
        wellPumpButton.className = `btn pump-control-button ${displayState ? 'btn-danger' : 'btn-primary'}`;
        wellPumpStatus.textContent = displayState ? 'ON' : 'OFF';
    }
}