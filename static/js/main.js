import { initState, updateState } from './modules/state.js';
import { initGPIO } from './modules/gpio.js';
import { initPumpControls } from './modules/pumps.js';
import { initModeControls } from './modules/modes.js';

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    initState();
    initGPIO();
    initPumpControls();
    initModeControls();
    
    // Set up regular updates
    updateState(); // Initial state update
    setInterval(updateState, 1000); // Regular state updates
});