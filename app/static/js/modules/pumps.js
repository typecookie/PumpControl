let wellPumpRunning = false;
let distPumpRunning = true;  // Default to ON for distribution pump
let wellPumpReverse = false;

export function initPumpControls() {
    console.log('Initializing pump controls');
    
    const wellPumpToggle = document.getElementById('manual-well-pump-toggle');
    const distPumpToggle = document.getElementById('manual-dist-pump-toggle');
    const reverseToggle = document.getElementById('well-pump-reverse-toggle');
    const outputInvertToggle = document.getElementById('well-pump-output-invert');
    
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
            console.log('Setting reverse mode:', enabled);
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
                    console.log('Reverse mode updated successfully:', enabled);
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

    // Add output inversion toggle handler
    if (outputInvertToggle) {
        outputInvertToggle.addEventListener('change', function() {
            const enabled = this.checked;
            console.log('Setting output inversion:', enabled);
            fetch('/api/pump/output-invert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled: enabled })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Output inversion updated successfully:', enabled);
                } else {
                    console.error('Failed to set output inversion:', data.message);
                    outputInvertToggle.checked = !enabled;
                }
            })
            .catch(error => {
                console.error('Error setting output inversion:', error);
                outputInvertToggle.checked = !enabled;
            });
        });
    }

    // Initial state fetch
    fetchInitialState();
}

function fetchInitialState() {
    console.log('Fetching initial state');
    Promise.all([
        fetch('/api/state').then(r => r.json()),
        fetch('/api/gpio_states').then(r => r.json())
    ])
    .then(([stateData, gpioData]) => {
        console.log('Initial state loaded:', { state: stateData, gpio: gpioData });
        
        // Update reverse mode toggle
        if (typeof stateData.well_pump_reverse !== 'undefined') {
            wellPumpReverse = stateData.well_pump_reverse;
            const reverseToggle = document.getElementById('well-pump-reverse-toggle');
            if (reverseToggle) {
                reverseToggle.checked = wellPumpReverse;
            }
        }

        // Update output inversion toggle
        const outputInvertToggle = document.getElementById('well-pump-output-invert');
        if (outputInvertToggle && gpioData.pumps?.well?.output_inverted !== undefined) {
            outputInvertToggle.checked = gpioData.pumps.well.output_inverted;
        }

        // Update pump states
        updatePumpDisplays(stateData);
    })
    .catch(error => console.error('Error fetching initial state:', error));
}

export function updatePumpDisplays(data) {
    console.log('Updating pump displays with data:', data);
    
    // Update pump status displays
    const wellStatus = data.well_pump_status;
    const distStatus = data.dist_pump_status;
    
    console.log('Pump states:', { well: wellStatus, dist: distStatus });
    
    document.getElementById('well-pump-status').textContent = wellStatus;
    document.getElementById('dist-pump-status').textContent = distStatus;

    // Update pump images
    updatePumpImage('well-pump', wellStatus);
    updatePumpImage('dist-pump', distStatus);

    // Update running states (store actual state)
    wellPumpRunning = wellStatus === 'ON';
    distPumpRunning = distStatus === 'ON';

    // Only show manual controls in CHANGEOVER mode
    const changeoverControls = document.getElementById('changeover-controls');
    if (changeoverControls) {
        const isChangeover = data.current_mode === 'CHANGEOVER';
        changeoverControls.style.display = isChangeover ? 'block' : 'none';
        
        if (isChangeover) {
            updateManualPumpControl('well', wellStatus);
            updateManualPumpControl('dist', distStatus);
        }
    }

    // Update reverse mode if provided
    if (typeof data.well_pump_reverse !== 'undefined') {
        wellPumpReverse = data.well_pump_reverse;
        const reverseToggle = document.getElementById('well-pump-reverse-toggle');
        if (reverseToggle) {
            reverseToggle.checked = wellPumpReverse;
        }
    }
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
    
    // Get the actual running state
    const running = pumpStatus === 'ON';
    
    // Calculate display state considering reverse mode
    const displayState = isWell && wellPumpReverse ? !running : running;
    
    console.log(`Updating ${pumpType} pump control:`, {
        actualState: running,
        displayState: displayState,
        reverseMode: isWell ? wellPumpReverse : false
    });
    
    const pumpButton = document.getElementById(buttonId);
    if (pumpButton) {
        pumpButton.textContent = displayState ? 
            `Stop ${isWell ? 'Well' : 'Distribution'} Pump` : 
            `Start ${isWell ? 'Well' : 'Distribution'} Pump`;
        pumpButton.className = `btn pump-control-button ${displayState ? 'btn-danger' : 'btn-primary'}`;
    }
    
    const statusElement = document.getElementById(statusId);
    if (statusElement) {
        statusElement.textContent = displayState ? 'ON' : 'OFF';
    }
}

function handlePumpToggle(pumpType) {
    const isWell = pumpType === 'well';
    const currentState = isWell ? wellPumpRunning : distPumpRunning;
    
    // For well pump in reverse mode, invert the desired state
    const desiredState = isWell && wellPumpReverse ? currentState : !currentState;
    
    console.log(`Toggling ${pumpType} pump:`, {
        currentState: currentState,
        desiredState: desiredState,
        reverseMode: isWell ? wellPumpReverse : false
    });
    
    const endpoint = isWell ? '/api/pump' : '/api/distribution_pump';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ running: desiredState })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(`${pumpType} pump toggle successful:`, data);
        } else {
            console.error('Failed to toggle pump:', data.message);
        }
    })
    .catch(error => {
        console.error('Error toggling pump:', error);
    });
}

function updatePumpButtonStates() {
    console.log('Updating pump button states');
    const wellPumpButton = document.getElementById('manual-well-pump-toggle');
    const wellPumpStatus = document.getElementById('manual-well-pump-status');
    
    if (wellPumpButton && wellPumpStatus) {
        const displayState = wellPumpReverse ? !wellPumpRunning : wellPumpRunning;
        wellPumpButton.textContent = displayState ? 'Stop Well Pump' : 'Start Well Pump';
        wellPumpButton.className = `btn pump-control-button ${displayState ? 'btn-danger' : 'btn-primary'}`;
        wellPumpStatus.textContent = displayState ? 'ON' : 'OFF';
    }
}