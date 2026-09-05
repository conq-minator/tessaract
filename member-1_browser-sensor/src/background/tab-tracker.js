/**
 * Tab Lifecycle Tracker
 * Observes tab activation, page loads, and tab closure with active duration tracking.
 */

class TabTracker {
    constructor(eventEmitter) {
        this.emit = eventEmitter;
        this.tabOpenTimes = new Map(); // tabId -> timestamp
        this.activeTabId = null;
        this.activeStartTime = Date.now();
    }

    init() {
        const api = globalThis.browser || globalThis.chrome;
        if (!api || !api.tabs) return;

        // Tab Activated (Focus switch)
        api.tabs.onActivated.addListener(async (activeInfo) => {
            try {
                const tab = await api.tabs.get(activeInfo.tabId);
                this._handleTabActivated(tab);
            } catch (e) {}
        });

        // Tab Updated (Page loaded or URL changed)
        api.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab && tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('about:')) {
                this._handlePageLoaded(tab);
            }
        });

        // Tab Removed (Closed)
        api.tabs.onRemoved.addListener((tabId, removeInfo) => {
            this._handleTabClosed(tabId);
        });
    }

    _handleTabActivated(tab) {
        if (!tab || !tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('about:')) return;
        
        const now = Date.now();
        this.activeTabId = tab.id;
        this.activeStartTime = now;
        if (!this.tabOpenTimes.has(tab.id)) {
            this.tabOpenTimes.set(tab.id, now);
        }

        this.emit('tab_activated', {
            tab_id: tab.id,
            url: tab.url,
            title: tab.title || '',
            window_id: tab.windowId
        });
    }

    _handlePageLoaded(tab) {
        this.emit('page_loaded', {
            tab_id: tab.id,
            url: tab.url,
            title: tab.title || '',
            load_time_ms: Date.now()
        });
    }

    _handleTabClosed(tabId) {
        const openTime = this.tabOpenTimes.get(tabId);
        const durationMs = openTime ? Date.now() - openTime : 0;
        this.tabOpenTimes.delete(tabId);

        this.emit('tab_closed', {
            tab_id: tabId,
            duration_ms: durationMs
        });
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TabTracker };
}
