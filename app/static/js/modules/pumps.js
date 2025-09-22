let wellPumpRunning = false;
let distPumpRunning = false;
let wellPumpReverse = false;

export function initPumpControls() {
    console.log('Initializing pump controls');
    
    // Find and add event listeners to pump control elements
    const wellPumpToggle = document.getElementById('manual-well-pump-toggle');
    const distPumpToggle = document.getElementById('manual-dist-pump-toggle');
    const reverseToggle = document.getElementById('well-pump-reverse-toggle');
    const outputInvertToggle = document.getElementById('well-pump-output-invert');
    
    if (wellPumpToggle) {
        wellPumpToggle.addEventListener('click', () => {
            console.log('Well pump toggle clicked');
            handlePumpToggle('well');
        });
    }
    
    if (distPumpToggle) {
        distPumpToggle.addEventListener('click', () => {
            console.log('Distribution pump toggle clicked');
            handlePumpToggle('dist');
        });
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
    console.log('Pump controls initialized');
}

function fetchInitialState() {
    console.log('Fetching initial pump state');
    Promise.all([
        fetch('/api/state').then(r => r.json()).catch(e => {
            console.error('Error fetching state:', e);
            return {};
        }),
        fetch('/api/gpio_states').then(r => r.json()).catch(e => {
            console.error('Error fetching GPIO states:', e);
            return {};
        })
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
    
    // Extract pump states using helper functions for resilience
    const wellStatus = getWellPumpState(data);
    const distStatus = getDistPumpState(data);
    
    console.log('Extracted pump states:', { well: wellStatus, dist: distStatus });
    
    // Update wellPumpRunning and distPumpRunning state variables
    wellPumpRunning = wellStatus === 'ON';
    distPumpRunning = distStatus === 'ON';

    // Update display elements if they exist
    updatePumpDisplayElement('well-pump-status', wellStatus);
    updatePumpDisplayElement('dist-pump-status', distStatus);

    // Update pump images
    updatePumpImage('well-pump', wellStatus);
    updatePumpImage('dist-pump', distStatus);

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

// Helper function to update a pump display element
function updatePumpDisplayElement(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = status;
        
        // Also update the element's class for styling if needed
        element.className = status === 'ON' 
            ? 'pump-status status-on' 
            : 'pump-status status-off';
    }
}

// Helper functions to extract pump states from various data structures
function getWellPumpState(data) {
    console.log('Extracting well pump state from:', data);
    
    // Try different property paths
    if (data.well_pump && data.well_pump.state) {
        return data.well_pump.state;
    } else if (data.well_pump_status) {
        return data.well_pump_status;
    } else if (data.gpio_states && data.gpio_states.pumps && data.gpio_states.pumps.well) {
        return data.gpio_states.pumps.well.value ? 'ON' : 'OFF';
    }
    return 'UNKNOWN';
}

function getDistPumpState(data) {
    console.log('Extracting dist pump state from:', data);
    
    // Try different property paths
    if (data.distribution_pump && data.distribution_pump.state) {
        return data.distribution_pump.state;
    } else if (data.dist_pump && data.dist_pump.state) {
        return data.dist_pump.state;
    } else if (data.dist_pump_status) {
        return data.dist_pump_status;
    } else if (data.gpio_states && data.gpio_states.pumps && data.gpio_states.pumps.distribution) {
        return data.gpio_states.pumps.distribution.value ? 'ON' : 'OFF';
    }
    return 'UNKNOWN';
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
        console.log(`${pumpType} pump toggle response:`, data);
        
        if (data.status === 'success') {
            // Update the UI immediately to reflect the change
            if (isWell) {
                wellPumpRunning = data.pump_running || desiredState;
                updateManualPumpControl('well', wellPumpRunning ? 'ON' : 'OFF');
                updatePumpDisplayElement('well-pump-status', wellPumpRunning ? 'ON' : 'OFF');
                updatePumpImage('well-pump', wellPumpRunning ? 'ON' : 'OFF');
            } else {
                distPumpRunning = data.pump_running || desiredState;
                updateManualPumpControl('dist', distPumpRunning ? 'ON' : 'OFF');
                updatePumpDisplayElement('dist-pump-status', distPumpRunning ? 'ON' : 'OFF');
                updatePumpImage('dist-pump', distPumpRunning ? 'ON' : 'OFF');
            }
            
            console.log(`${pumpType} pump toggle successful`);
        } else {
            console.error('Failed to toggle pump:', data.message);
            // Show error to user
            showToast('error', `Failed to ${desiredState ? 'start' : 'stop'} ${pumpType} pump: ${data.message || 'Unknown error'}`);
        }
    })
    .catch(error => {
        console.error('Error toggling pump:', error);
        showToast('error', `Error toggling ${pumpType} pump: ${error}`);
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

function showToast(type, message) {
    // Create toast element
    const toastDiv = document.createElement('div');
    toastDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed bottom-0 end-0 m-3`;
    toastDiv.style.zIndex = '1050';
    toastDiv.textContent = message;
    document.body.appendChild(toastDiv);
    
    // Remove after delay
    setTimeout(() => {
        if (document.body.contains(toastDiv)) {
            toastDiv.remove();
        }
    }, 3000);
}