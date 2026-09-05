/**
 * Tesseract Browser Sensor - Background Entry Point
 * Orchestrates Tab, Search, YouTube, Bookmark, and Navigation trackers
 * and streams standardized TesseractEvent JSON to Core Engine over WebSocket.
 */

// Load dependencies if running in Chromium Service Worker context
if (typeof formatTesseractEvent === 'undefined' && typeof importScripts === 'function') {
    try {
        importScripts(
            '../browser-polyfill.js',
            'event-formatter.js',
            'ws-client.js',
            'tab-tracker.js',
            'search-monitor.js',
            'youtube-detector.js',
            'bookmark-tracker.js',
            'navigation-tracker.js'
        );
    } catch (e) {
        console.error('[TesseractSensor] Failed to import scripts:', e);
    }
}

(function () {
    const api = globalThis.browser || globalThis.chrome;
    let isTrackingEnabled = true;

    // Initialize WebSocket client with token authentication
    const SHARED_SECRET = 'rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk';
    const wsClient = new TesseractWSClient(`ws://localhost:9700/events?token=${SHARED_SECRET}`, 100);
    wsClient.connect();

    // Chromium (Brave/Chrome) Service Worker Keepalive & Reconnect
    if (api && api.alarms) {
        api.alarms.create('tesseract_sensor_keepalive', { periodInMinutes: 0.5 });
        api.alarms.onAlarm.addListener((alarm) => {
            if (alarm.name === 'tesseract_sensor_keepalive' && !wsClient.isConnected) {
                console.log('[TesseractSensor] Keepalive alarm check - reconnecting WS...');
                wsClient.connect();
            }
        });
    }
    setInterval(() => {
        if (!wsClient.isConnected) {
            wsClient.connect();
        }
    }, 15000);

    // Central event dispatcher
    function emitTesseractEvent(eventType, payload, metadata = {}) {
        if (!isTrackingEnabled) {
            console.log(`[TesseractSensor] Tracking paused, dropped event: ${eventType}`);
            return;
        }

        const event = formatTesseractEvent(eventType, payload, metadata);
        console.log(`[TesseractSensor] Event [${eventType}]:`, payload);
        wsClient.sendEvent(event);
    }

    // Initialize Trackers
    const tabTracker = new TabTracker(emitTesseractEvent);
    tabTracker.init();

    const searchMonitor = new SearchMonitor(emitTesseractEvent);
    searchMonitor.init();

    const youtubeDetector = new YouTubeDetector(emitTesseractEvent);
    youtubeDetector.init();

    const bookmarkTracker = new BookmarkTracker(emitTesseractEvent);
    bookmarkTracker.init();

    const navigationTracker = new NavigationTracker(emitTesseractEvent);
    navigationTracker.init();

    // Communication with Popup UI
    if (api && api.runtime && api.runtime.onMessage) {
        api.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (!request) return;

            if (request.type === 'GET_SENSOR_STATUS') {
                sendResponse({
                    ...wsClient.getStatus(),
                    isTrackingEnabled: isTrackingEnabled
                });
                return true;
            } else if (request.type === 'TOGGLE_TRACKING') {
                isTrackingEnabled = !isTrackingEnabled;
                if (api.storage && api.storage.local) {
                    api.storage.local.set({ isTrackingEnabled });
                }
                sendResponse({
                    isTrackingEnabled: isTrackingEnabled
                });
                return true;
            } else if (request.type === 'RECONNECT_WS') {
                wsClient.connect();
                sendResponse({ status: 'reconnecting' });
                return true;
            }
        });
    }

    // Load initial storage settings
    if (api && api.storage && api.storage.local) {
        api.storage.local.get(['isTrackingEnabled'], (res) => {
            if (typeof res.isTrackingEnabled === 'boolean') {
                isTrackingEnabled = res.isTrackingEnabled;
            }
        });
    }

    console.log('[TesseractSensor] Background services initialized.');
})();
