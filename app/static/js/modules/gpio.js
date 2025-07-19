export function initGPIO() {
    setInterval(updateGPIOStates, 1000);
    
    // Set up pump inversion buttons
    document.querySelectorAll('.pump-invert-btn').forEach(button => {
        button.addEventListener('click', function() {
            const pump = this.getAttribute('data-pump');
            togglePumpInvert(pump);
        });
    });
}

function updateGPIOStates() {
    fetch('/api/gpio_states')
        .then(response => response.json())
        .then(data => {
            updateSummerTankGPIO(data.summer_tank);
            updateWinterTankGPIO(data.winter_tank);
            updatePumpGPIO(data.pumps);
        })
        .catch(error => console.error('Error updating GPIO states:', error));
}

function updateSummerTankGPIO(data) {
    const html = formatGPIOState('High', data.high) +
                formatGPIOState('Low', data.low) +
                formatGPIOState('Empty', data.empty);
    document.getElementById('summer-gpio-states').innerHTML = html;
}

function updateWinterTankGPIO(data) {
    const html = formatGPIOState('High', data.high) +
                formatGPIOState('Low', data.low);
    document.getElementById('winter-gpio-states').innerHTML = html;
}

function updatePumpGPIO(data) {
    let html = '';
    if (data.well) {
        html += `<p>Well Pump (Pin ${data.well.pin}): Value: ${data.well.value}`;
        if (typeof data.well.reverse_mode !== 'undefined') {
            html += ` (Inverted: ${data.well.reverse_mode})`;
        }
        html += '</p>';
    }
    if (data.distribution) {
        html += `<p>Distribution Pump (Pin ${data.distribution.pin}): Value: ${data.distribution.value}</p>`;
    }
    document.getElementById('pump-gpio-states').innerHTML = html;
}

function togglePumpInvert(pump) {
    if (pump !== 'well') {
        showToast('error', 'Pump inversion is only supported for well pump');
        return;
    }

    // Get current state from GPIO display
    const wellPumpElement = document.querySelector('#pump-gpio-states p:first-child');
    const currentState = wellPumpElement && wellPumpElement.textContent.includes('(Inverted: true)');
    
    fetch('/api/well-pump-reverse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled: !currentState })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('success', `Well pump inversion ${data.reverse_mode ? 'enabled' : 'disabled'}`);
            // Refresh GPIO states immediately
            updateGPIOStates();
        } else {
            showToast('error', data.message);
        }
    })
    .catch(error => {
        showToast('error', 'Error toggling pump inversion: ' + error);
    });
}

function showToast(type, message) {
    const toastDiv = document.createElement('div');
    toastDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed bottom-0 end-0 m-3`;
    toastDiv.style.zIndex = '1050';
    toastDiv.textContent = message;
    document.body.appendChild(toastDiv);
    setTimeout(() => toastDiv.remove(), 3000);
}

function formatGPIOState(name, data) {
    return `<p>${name} (Pin ${data.pin}): 
            Raw: ${data.raw_value} 
            Inverted: ${data.inverted_value}</p>`;
}