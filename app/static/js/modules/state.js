import { updateTankDisplays } from './tanks.js';
import { updatePumpDisplays } from './pumps.js';
import { updateModeDisplay } from './modes.js';

export function initState() {
    console.log('Initializing state module');
    // Any initial state setup if needed
}

export function updateState() {
    console.log('Starting state update...');
    
    fetch('/api/state')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('State data received:', data);
            
            // Check if we have a modal showing - if so, don't update mode display
            const modeModal = document.getElementById('modeConfirmModal');
            const isModalShowing = modeModal?.classList.contains('show');
            
            if (!isModalShowing && data.current_mode) {
                updateModeDisplay(data.current_mode);
            }
            
            // Update tanks and pumps with enhanced error handling
            try {
                updateTankDisplays(data);
            } catch (error) {
                console.error('Error updating tank displays:', error);
            }
            
            try {
                updatePumpDisplays(data);
            } catch (error) {
                console.error('Error updating pump displays:', error);
            }
            
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