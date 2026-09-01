/**
 * Chart.js wrapper components for Tesseract Dashboard
 * To be used in analytics views when needed
 */

class TesseractCharts {
    static getThemeColors() {
        const style = getComputedStyle(document.documentElement);
        return {
            text: style.getPropertyValue('--text-secondary').trim(),
            grid: style.getPropertyValue('--border-primary').trim(),
            accent: style.getPropertyValue('--accent-primary').trim(),
            accentMuted: style.getPropertyValue('--accent-muted').trim()
        };
    }

    static createLineChart(ctx, data, labels, title) {
        const colors = this.getThemeColors();
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: title,
                    data: data,
                    borderColor: colors.accent,
                    backgroundColor: colors.accentMuted,
                    borderWidth: 2,
                    pointBackgroundColor: colors.accent,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { color: colors.grid, drawBorder: false },
                        ticks: { color: colors.text }
                    },
                    y: {
                        grid: { color: colors.grid, drawBorder: false },
                        ticks: { color: colors.text }
                    }
                }
            }
        });
    }
}

window.TesseractCharts = TesseractCharts;

// Update charts when theme changes
window.addEventListener('theme-changed', () => {
    // Re-render logic would go here if charts are active
});
