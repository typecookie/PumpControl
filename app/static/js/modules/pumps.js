let wellPumpRunning = false;
let distPumpRunning = true;  // Default to ON for distribution pump

export function initPumpControls() {
    const wellPumpToggle = document.getElementById('manual-well-pump-toggle');
    const distPumpToggle = document.getElementById('manual-dist-pump-toggle');
    
    if (wellPumpToggle) {
        wellPumpToggle.addEventListener('click', () => handlePumpToggle('well'));
    }
    
    if (distPumpToggle) {
        distPumpToggle.addEventListener('click', () => handlePumpToggle('dist'));
    }

    // Initial update of pump displays
    updatePumpDisplays({
        well_pump_status: 'OFF',
        dist_pump_status: 'ON',
        current_mode: 'CHANGEOVER'
    });
}

export function updatePumpDisplays(data) {
    document.getElementById('well-pump-status').textContent = data.well_pump_status;
    document.getElementById('dist-pump-status').textContent = data.dist_pump_status;

    // Update pump images if they exist
    updatePumpImage('well-pump', data.well_pump_status);
    updatePumpImage('dist-pump', data.dist_pump_status);

    // Only show manual controls in CHANGEOVER mode
    const changeoverControls = document.getElementById('changeover-controls');
    if (changeoverControls) {
        changeoverControls.style.display = data.current_mode === 'CHANGEOVER' ? 'block' : 'none';
        
        if (data.current_mode === 'CHANGEOVER') {
            updateManualPumpControl('well', data.well_pump_status);
            updateManualPumpControl('dist', data.dist_pump_status);
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
    const pumpRunning = pumpStatus === 'ON';
    
    const pumpButton = document.getElementById(buttonId);
    if (pumpButton) {
        pumpButton.textContent = pumpRunning ? `Stop ${isWell ? 'Well' : 'Distribution'} Pump` : `Start ${isWell ? 'Well' : 'Distribution'} Pump`;
        pumpButton.className = `btn pump-control-button ${pumpRunning ? 'btn-danger' : 'btn-primary'}`;
    }
    
    const statusElement = document.getElementById(statusId);
    if (statusElement) {
        statusElement.textContent = pumpStatus;
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
    const newState = !currentState;
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
                wellPumpRunning = newState;
            } else {
                distPumpRunning = newState;
            }
            
            // Update the UI
            const status = data.pump_running ? 'ON' : 'OFF';
            updateManualPumpControl(pumpType, status);
            document.getElementById(`${pumpType}-pump-status`).textContent = status;
        } else {
            console.error('Failed to toggle pump:', data.message);
        }
    })
    .catch(error => {
        console.error('Error toggling pump:', error);
    });
}