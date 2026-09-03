/**
 * app.js - Main Application Initialization & Robust Navigation
 */

const App = {
    state: {
        context: null,
        theme: localStorage.getItem('tesseract-theme') || 'dark'
    },
    pollTimer: null,

    init() {
        // Setup Theme
        this.applyTheme(this.state.theme);
        
        // Highlight active navigation link
        this.setupNavigation();
        
        // Initialize global components (modals, toasts)
        if (window.Notifications) window.Notifications.init();
        
        // Hide global loader immediately
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 100);
        }
        
        // Load initial context
        this.loadGlobalState();
        
        // Use lightweight 5s polling instead of persistent SSE sockets
        // This guarantees 0 socket exhaustion and 100% responsiveness on infinite clicks
        this.startPolling();

        // Global Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && window.Modal) {
                window.Modal.hide();
            }
        });
    },

    startPolling() {
        if (this.pollTimer) clearInterval(this.pollTimer);
        this.pollTimer = setInterval(() => {
            this.loadGlobalState();
        }, 5000);
    },

    async loadGlobalState() {
        try {
            this.state.context = await window.API.getContext();
            this.updateContextUI();
        } catch (e) {
            // Silently ignore background polling errors
        }
    },

    setupNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (currentPath === href || (currentPath === '/' && href === '/overview')) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    },

    updateContextUI() {
        // Context updates for header
    },

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('tesseract-theme', theme);
        window.dispatchEvent(new CustomEvent('theme-changed', { detail: { theme } }));
    },
    
    toggleTheme() {
        const newTheme = this.state.theme === 'dark' ? 'light' : 'dark';
        this.state.theme = newTheme;
        this.applyTheme(newTheme);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

window.App = App;
