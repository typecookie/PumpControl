let manualPumpRunning = false;

export function initPumpControls() {
    const pumpToggle = document.getElementById('manual-pump-toggle');
    if (pumpToggle) {
        pumpToggle.addEventListener('click', handlePumpToggle);
    }
}

export function updatePumpDisplays(data) {
    document.getElementById('well-pump-status').textContent = data.well_pump_status;
    document.getElementById('dist-pump-status').textContent = data.dist_pump_status;

    if (data.current_mode === 'CHANGEOVER') {
        updateManualPumpControl(data.well_pump_status);
    }
}

function updatePumpImage(pumpId, status) {
    const imageElement = document.getElementById(`${pumpId}-image`);
    if (imageElement) {
        const imagePath = status.toLowerCase() === 'on' 
            ? '/static/img/pump_on.jpg' 
            : '/static/img/pump_off.jpg';
        imageElement.src = imagePath;
    }
}

// Use this function whenever you update the pump status
function updatePumpStatus(data) {
    // Update well pump
    const wellPumpStatus = document.getElementById('well-pump-status');
    if (wellPumpStatus) {
        wellPumpStatus.textContent = data.well_pump_status;
        updatePumpImage('well-pump', data.well_pump_status);
    }
    
    // Update distribution pump
    const distPumpStatus = document.getElementById('dist-pump-status');
    if (distPumpStatus) {
        distPumpStatus.textContent = data.dist_pump_status;
        updatePumpImage('dist-pump', data.dist_pump_status);
    }
}

function updateManualPumpControl(pumpStatus) {
    const pumpButton = document.getElementById('manual-pump-toggle');
    manualPumpRunning = pumpStatus === 'ON';
    if (pumpButton) {
        pumpButton.textContent = manualPumpRunning ? 'Stop Well Pump' : 'Start Well Pump';
    }
    document.getElementById('manual-pump-status').textContent = pumpStatus;
}

function handlePumpToggle() {
    manualPumpRunning = !manualPumpRunning;
    
    fetch('/api/manual_pump', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ running: manualPumpRunning })
    })
    .then(response => response.json())
    .then(handlePumpResponse)  // This function is called but not defined
    .catch(handlePumpError);   // This function is called but not defined
}

function handlePumpResponse(data) {
    if (data.status === 'success') {
        // Update the pump status based on server response
        manualPumpRunning = data.pump_running;
        updateManualPumpControl(manualPumpRunning ? 'ON' : 'OFF');
    } else if (data.status === 'error') {
        console.error('Pump control error:', data.message);
        // Revert the button state
        manualPumpRunning = !manualPumpRunning;
        updateManualPumpControl(manualPumpRunning ? 'ON' : 'OFF');
        alert(data.message);
    }
}

function handlePumpError(error) {
    console.error('Error controlling pump:', error);
    // Revert the button state on error
    manualPumpRunning = !manualPumpRunning;
    updateManualPumpControl(manualPumpRunning ? 'ON' : 'OFF');
    alert('Failed to control pump. Please try again.');
}