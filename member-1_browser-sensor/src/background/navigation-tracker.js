/**
 * Navigation Pattern Tracker
 * Captures from_url -> to_url transitions and repeated visits.
 */

class NavigationTracker {
    constructor(eventEmitter) {
        this.emit = eventEmitter;
        this.lastUrlPerTab = new Map();
    }

    init() {
        const api = globalThis.browser || globalThis.chrome;
        if (!api || !api.webNavigation) return;

        api.webNavigation.onCommitted.addListener((details) => {
            if (details.frameId !== 0) return; // Top-level frame only

            const tabId = details.tabId;
            const toUrl = details.url;
            const fromUrl = this.lastUrlPerTab.get(tabId) || null;
            this.lastUrlPerTab.set(tabId, toUrl);

            if (fromUrl && fromUrl !== toUrl && !toUrl.startsWith('chrome://') && !toUrl.startsWith('about:')) {
                this.emit('navigation', {
                    tab_id: tabId,
                    from_url: fromUrl,
                    to_url: toUrl,
                    transition_type: details.transitionType
                });
            }
        });

        if (api.tabs) {
            api.tabs.onRemoved.addListener((tabId) => {
                this.lastUrlPerTab.delete(tabId);
            });
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NavigationTracker };
}
