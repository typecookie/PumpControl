import { updateTankDisplays } from './tanks.js';
import { updatePumpDisplays } from './pumps.js';
import { updateModeDisplay } from './modes.js';

export function initState() {
    // Initial state setup if needed
}

export function updateState() {
    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            console.log('State update received:', data);
            
            // Update different components
            updateModeDisplay(data.current_mode);
            updateTankDisplays(data);
            updatePumpDisplays(data);
        })
        .catch(error => {
            console.error('Error updating state:', error);
        });
}

// Helper function for stats formatting
export function formatStats(stats) {
    return `
        <p>Today's Runtime: ${stats.today_runtime}</p>
        <p>Today's Gallons: ${stats.today_gallons}</p>
        <p>Week Runtime: ${stats.week_runtime}</p>
        <p>Week Gallons: ${stats.week_gallons}</p>
        <p>Month Runtime: ${stats.month_runtime}</p>
        <p>Month Gallons: ${stats.month_gallons}</p>
    `;
}