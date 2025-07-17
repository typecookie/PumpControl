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

        // Send each configuration separately
        Object.entries(configurations).forEach(([alertType, channels]) => {
            fetch('/api/alerts/types', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    alert_type: alertType,
                    channels: channels
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast('success', 'Alert types configuration saved');
                } else {
                    showToast('error', 'Error saving alert types: ' + data.message);
                }
            })
            .catch(error => {
                showToast('error', 'Error saving alert types: ' + error);
            });
        });
    });

    // Rate limits configuration
    document.getElementById('rate-limits-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        // Set default rate limits for specific channels
        data['tank_error'] = Math.min(data['tank_error'], 600);  // 10 minutes
        data['system_error'] = Math.min(data['system_error'], 600);  // 10 minutes
        data['tank_empty'] = Math.min(data['tank_empty'], 3600);  // 1 hour

        Object.entries(data).forEach(([alertType, seconds]) => {
            fetch('/api/alerts/rate-limits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    alert_type: alertType,
                    seconds: parseInt(seconds)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast('success', 'Rate limits saved successfully');
                } else {
                    showToast('error', 'Error saving rate limits: ' + data.message);
                }
            })
            .catch(error => {
                showToast('error', 'Error saving rate limits: ' + error);
            });
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
        .then(response => response.json())
        .then(data => {
            // Populate channel configurations
            Object.entries(data.channels).forEach(([channel, config]) => {
                const form = document.querySelector(`#${channel}-config-form`);
                if (form) {
                    Object.entries(config).forEach(([key, value]) => {
                        const input = form.querySelector(`[name="${key}"]`);
                        if (input) {
                            if (key === 'to_emails' && Array.isArray(value)) {
                                input.value = value.join(', ');
                            } else if (key === 'password') {
                                input.value = '********';
                            } else {
                                input.value = value;
                            }
                        }
                    });
                }
            });

            // Populate alert type checkboxes
            Object.entries(data.alert_types).forEach(([alertType, channels]) => {
                channels.forEach(channel => {
                    const checkbox = document.querySelector(`#${alertType}_${channel}`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });
            });
        })
        .catch(error => {
            showToast('error', 'Error loading configuration: ' + error);
        });
}

function showToast(type, message) {
    const toast = document.getElementById('alertToast');
    const toastBody = toast.querySelector('.toast-body');
    
    toast.classList.remove('bg-success', 'bg-danger');
    toast.classList.add(type === 'success' ? 'bg-success' : 'bg-danger');
    toastBody.textContent = message;
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}