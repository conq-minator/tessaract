/**
 * Settings Page Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // Set theme radio button based on current app state
    const currentTheme = window.App.state.theme;
    const themeRadios = document.querySelectorAll('input[name="theme"]');
    themeRadios.forEach(r => {
        if (r.value === currentTheme) r.checked = true;
    });
});

async function saveSettings() {
    // In a real implementation this would send a POST/PUT to the API
    const level = document.getElementById('autonomy-select').value;
    
    // Check if level > 3 (requires confirmation dialog per specs)
    if (parseInt(level) >= 4) {
        const confirmed = await window.Modal.confirm({
            title: 'High Autonomy Warning',
            message: `You are about to enable Level ${level} Autonomy. Tesseract will be able to take consequential actions on your behalf with supervision. Do you wish to proceed?`,
            confirmText: 'Enable',
            type: 'warning'
        });
        
        if (!confirmed) {
            // Revert select back if cancelled
            document.getElementById('autonomy-select').value = "2"; 
            return;
        }
    }
    
    if (window.Notifications) {
        window.Notifications.success('Settings Saved', 'Your preferences have been updated successfully.');
    }
}
