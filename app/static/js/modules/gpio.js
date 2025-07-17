export function initGPIO() {
    setInterval(updateGPIOStates, 1000);
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
    // data.well and data.distribution are objects, not array items
    let html = '';
    if (data.well) {
        html += `<p>Well Pump (Pin ${data.well.pin}): Value: ${data.well.value}</p>`;
    }
    if (data.distribution) {
        html += `<p>Distribution Pump (Pin ${data.distribution.pin}): Value: ${data.distribution.value}</p>`;
    }
    document.getElementById('pump-gpio-states').innerHTML = html;
}

function formatGPIOState(name, data) {
    return `<p>${name} (Pin ${data.pin}): 
            Raw: ${data.raw_value} 
            Inverted: ${data.inverted_value}</p>`;
}