// Function to update the tank displays
export function updateTankDisplays(data) {
    console.log('Updating tank displays with data:', data);

    // Check for well_pump_status and dist_pump_status in the data
    const wellPumpStatus = data.well_pump ? data.well_pump.state : (data.well_pump_status || 'UNKNOWN');
    const distPumpStatus = data.distribution_pump ? data.distribution_pump.state : (data.dist_pump_status || 'UNKNOWN');

    // Create tank state objects
    const winterTankState = determineWinterTankState(data);
    const summerTankState = determineSummerTankState(data);

    // Update the display with our tank states
    const summerStateEl = document.getElementById('summer-state');
    const winterStateEl = document.getElementById('winter-state');

    if (summerStateEl) {
        summerStateEl.textContent = summerTankState;
    }
    
    if (winterStateEl) {
        winterStateEl.textContent = winterTankState;
    }

    // For statistics - only if we have them
    updateTankStatsIfAvailable(data);

    // Log for debugging
    console.log('Updated tank states:', {
        summer: summerTankState,
        winter: winterTankState,
        wellPump: wellPumpStatus,
        distPump: distPumpStatus
    });
}

// Helper function to determine winter tank state from GPIO data
function determineWinterTankState(data) {
    // First check if we have a direct winter_tank.state property
    if (data.winter_tank && data.winter_tank.state) {
        return data.winter_tank.state;
    }
    
    // Otherwise extract from GPIO states if available
    if (data.gpio_states && data.gpio_states.winter_tank) {
        const high = data.gpio_states.winter_tank.high.raw_value;
        const low = data.gpio_states.winter_tank.low.raw_value;
        
        if (high) {
            return 'HIGH';
        } else if (!low) {
            return 'LOW';
        } else if (low && !high) {
            return 'MID';
        } else {
            return 'ERROR';
        }
    }
    
    return 'UNKNOWN';
}

// Helper function to determine summer tank state from GPIO data
function determineSummerTankState(data) {
    // First check if we have a direct summer_tank.state property
    if (data.summer_tank && data.summer_tank.state) {
        return data.summer_tank.state;
    }
    
    // Otherwise extract from GPIO states if available
    if (data.gpio_states && data.gpio_states.summer_tank) {
        const high = data.gpio_states.summer_tank.high.raw_value;
        const low = data.gpio_states.summer_tank.low.raw_value;
        const empty = data.gpio_states.summer_tank.empty.raw_value;
        
        if (high) {
            return 'HIGH';
        } else if (low && !high) {
            return 'MID';
        } else if (empty && !low && !high) {
            return 'LOW';
        } else if (!empty && !low && !high) {
            return 'EMPTY';
        } else {
            return 'ERROR';
        }
    }
    
    return 'UNKNOWN';
}

// Update tank statistics if available
function updateTankStatsIfAvailable(data) {
    try {
        if (data.summer_tank && data.summer_tank.stats) {
            updateTankStats('summer-stats', data.summer_tank.stats);
        }
        
        if (data.winter_tank && data.winter_tank.stats) {
            updateTankStats('winter-stats', data.winter_tank.stats);
        }
    } catch (error) {
        console.error('Error updating tank stats:', error);
    }
}

// Helper function to update tank statistics
function updateTankStats(elementId, stats) {
    const statsElement = document.getElementById(elementId);
    if (!statsElement || !stats) return;
    
    // Check if we have any stats to display
    const hasStats = Object.keys(stats).length > 0;
    
    if (hasStats) {
        // Display whatever stats are available
        let html = '<h5 class="mt-3">Statistics</h5>';
        
        if ('today_runtime' in stats) html += `<p>Today's Runtime: ${stats.today_runtime}</p>`;
        if ('today_gallons' in stats) html += `<p>Today's Gallons: ${stats.today_gallons}</p>`;
        if ('week_runtime' in stats) html += `<p>Week Runtime: ${stats.week_runtime}</p>`;
        if ('week_gallons' in stats) html += `<p>Week Gallons: ${stats.week_gallons}</p>`;
        if ('month_runtime' in stats) html += `<p>Month Runtime: ${stats.month_runtime}</p>`;
        if ('month_gallons' in stats) html += `<p>Month Gallons: ${stats.month_gallons}</p>`;
        
        statsElement.innerHTML = html;
    } else {
        statsElement.innerHTML = '<p>Statistics not available</p>';
    }
}