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
    let html = '';
    for (const pump of data) {
        html += `<p>${pump.name} (Pin ${pump.pin}): 
                Raw: ${pump.raw_value} 
                Inverted: ${pump.inverted_value}</p>`;
    }
    document.getElementById('pump-gpio-states').innerHTML = html;
}

function formatGPIOState(name, data) {
    return `<p>${name} (Pin ${data.pin}): 
            Raw: ${data.raw_value} 
            Inverted: ${data.inverted_value}</p>`;
}