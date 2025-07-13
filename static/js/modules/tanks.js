// Function to update the tank displays
export function updateTankDisplays(data) {
    // Update tank states
    document.getElementById('summer-state').textContent = data.summer_tank.state;
    document.getElementById('winter-state').textContent = data.winter_tank.state;

    // Update tank statistics
    updateTankStats('summer-stats', data.summer_tank.stats);
    updateTankStats('winter-stats', data.winter_tank.stats);
}

// Helper function to update tank statistics
function updateTankStats(elementId, stats) {
    const statsElement = document.getElementById(elementId);
    if (statsElement) {
        statsElement.innerHTML = `
            <h5 class="mt-3">Statistics</h5>
            <p>Today's Runtime: ${stats.today_runtime}</p>
            <p>Today's Gallons: ${stats.today_gallons}</p>
            <p>Week Runtime: ${stats.week_runtime}</p>
            <p>Week Gallons: ${stats.week_gallons}</p>
            <p>Month Runtime: ${stats.month_runtime}</p>
            <p>Month Gallons: ${stats.month_gallons}</p>
        `;
    }
}