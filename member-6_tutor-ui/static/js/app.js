/**
 * app.js - Main Application Initialization and Router
 */

const App = {
    state: {
        context: null,
        theme: localStorage.getItem('tesseract-theme') || 'dark'
    },

    init() {
        console.log("Tesseract UI Initializing...");
        
        // Setup Theme
        this.applyTheme(this.state.theme);
        
        // Highlight active navigation link
        this.setupNavigation();
        
        // Initialize global components (modals, toasts)
        if (window.Notifications) window.Notifications.init();
        
        // Hide global loader
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 300);
        }
        
        // Load initial context
        this.loadGlobalState();
        
        // Connect SSE for real-time notifications
        this.connectSSE();
        
        // Global Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && window.Modal) {
                window.Modal.hide();
            }
        });
    },

    connectSSE() {
        if (!window.EventSource) return;
        
        const evtSource = new EventSource('/api/stream');
        
        evtSource.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                if (data.type === "toast" && window.Notifications) {
                    window.Notifications.show(
                        data.data.title || "Notification", 
                        data.data.message || "", 
                        data.data.type || "info"
                    );
                } else if (data.type === "refresh_context") {
                    this.loadGlobalState();
                }
            } catch (err) {
                console.error("SSE parsing error:", err);
            }
        };
        
        evtSource.onerror = (err) => {
            console.error("SSE connection error", err);
        };
    },

    async loadGlobalState() {
        try {
            this.state.context = await window.API.getContext();
            this.updateContextUI();
        } catch (e) {
            console.error("Failed to load global context on init", e);
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
        // Find header element to inject subject context if needed
        const headerTitle = document.querySelector('.page-header h1');
        if (headerTitle && this.state.context) {
            // Optional: Append current subject to header
            // headerTitle.innerHTML += ` <span class="badge badge-primary">${this.state.context.subject}</span>`;
        }
    },

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('tesseract-theme', theme);
        
        // Trigger event for charts or graphs to re-render if needed
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
