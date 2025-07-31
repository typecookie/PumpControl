import { updateTankDisplays } from './tanks.js';
import { updatePumpDisplays } from './pumps.js';
import { updateModeDisplay } from './modes.js';

export function initState() {
    // Initial state setup if needed
}

export function updateState() {
    console.log('Starting state update...');
    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            console.log('State data received:', data);
            
            // Update mode if modal isn't showing
            if (!document.getElementById('modeConfirmModal')?.classList.contains('show')) {
                updateModeDisplay(data.current_mode);
            }
            
            // Update tanks and pumps
            updateTankDisplays(data);
            updatePumpDisplays(data);
            
            // Update reverse mode toggle if it exists
            const reverseToggle = document.getElementById('well-pump-reverse-toggle');
            if (reverseToggle && typeof data.well_pump_reverse !== 'undefined') {
                reverseToggle.checked = data.well_pump_reverse;
            }
        })
        .catch(error => {
            console.error('Error in updateState:', error);
        });
}