document.addEventListener('DOMContentLoaded', function() {
    // Load current configuration
    loadConfiguration();

    // Channel configuration forms
    document.querySelectorAll('.channel-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            const data = {
                channel: formData.get('channel'),
                config: Object.fromEntries(formData.entries())
            };
            delete data.config.channel;

            // For email, convert to_emails to array
            if (data.channel === 'email' && data.config.to_emails) {
                data.config.to_emails = data.config.to_emails.split(',').map(email => email.trim());
            }

            fetch('/api/alerts/channels', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast('success', 'Channel configuration saved successfully');
                } else {
                    showToast('error', 'Error saving channel configuration: ' + data.message);
                }
            })
            .catch(error => {
                showToast('error', 'Error saving channel configuration: ' + error);
            });
        });
    });

    // Alert types configuration
    document.getElementById('alert-types-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const configurations = {};
        
        document.querySelectorAll('.channel-checkboxes').forEach(div => {
            const alertType = div.querySelector('input').name;
            const selectedChannels = Array.from(div.querySelectorAll('input:checked'))
                                       .map(input => input.value);
            configurations[alertType] = selectedChannels;
        });

        const savePromises = Object.entries(configurations).map(([alertType, channels]) => {
            return fetch('/api/alerts/types', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    alert_type: alertType,
                    channels: channels
                })
            })
            .then(async response => {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    if (!response.ok) {
                        throw new Error(data.message || `Error saving ${alertType}`);
                    }
                    return data;
                } else {
                    throw new Error(`Invalid response type for ${alertType}`);
                }
            });
        });

        Promise.all(savePromises)
            .then(() => {
                showToast('success', 'All alert types saved successfully');
            })
            .catch(error => {
                console.error('Error saving alert types:', error);
                showToast('error', 'Error saving alert types: ' + error.message);
            });
    });

    // Test channel buttons
    document.querySelectorAll('.test-channel').forEach(button => {
        button.addEventListener('click', function() {
            const channel = this.dataset.channel;
            fetch('/api/alerts/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ channel: channel })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast('success', `Test notification sent to ${channel}`);
                } else {
                    showToast('error', `Error sending test to ${channel}: ${data.message}`);
                }
            })
            .catch(error => {
                showToast('error', `Error sending test to ${channel}: ${error}`);
            });
        });
    });
});

function loadConfiguration() {
    fetch('/api/alerts/config')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'error') {
                throw new Error(data.message || 'Unknown error occurred');
            }

            // Ensure we have objects to work with
            const channels = data.channels || {};
            const alertTypes = data.alert_types || {};
            const rateLimits = data.rate_limits || {};

            // Populate channel configurations
            Object.entries(channels).forEach(([channel, config]) => {
                const form = document.querySelector(`#${channel}-config-form`);
                if (form && config) {
                    Object.entries(config).forEach(([key, value]) => {
                        const input = form.querySelector(`[name="${key}"]`);
                        if (input) {
                            if (key === 'to_emails' && Array.isArray(value)) {
                                input.value = value.join(', ');
                            } else if (key === 'password' && value) {
                                input.value = '********';
                            } else if (value !== null && value !== undefined) {
                                input.value = value;
                            }
                        }
                    });
                }
            });

            // Populate alert type checkboxes
            Object.entries(alertTypes).forEach(([alertType, channels]) => {
                if (Array.isArray(channels)) {
                    channels.forEach(channel => {
                        const checkbox = document.querySelector(`#${alertType}_${channel}`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });
                }
            });

            // Populate rate limits if they exist
            Object.entries(rateLimits).forEach(([alertType, limit]) => {
                const input = document.querySelector(`input[name="${alertType}"]`);
                if (input && limit !== null && limit !== undefined) {
                    input.value = limit;
                }
            });
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            showToast('error', 'Error loading configuration: ' + error.message);
        });
}

function showToast(type, message) {
    const toast = document.getElementById('alertToast');
    if (!toast) {
        console.error('Toast element not found');
        return;
    }
    
    const toastBody = toast.querySelector('.toast-body');
    if (!toastBody) {
        console.error('Toast body element not found');
        return;
    }
    
    toast.classList.remove('bg-success', 'bg-danger');
    toast.classList.add(type === 'success' ? 'bg-success' : 'bg-danger');
    toastBody.textContent = message;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}