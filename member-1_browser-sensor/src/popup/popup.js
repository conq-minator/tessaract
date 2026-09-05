/**
 * Tesseract Browser Sensor - Popup Controller
 */

(function () {
    const api = globalThis.browser || globalThis.chrome;

    const connBadge = document.getElementById('conn-badge');
    const connDot = document.getElementById('conn-dot');
    const connText = document.getElementById('conn-text');
    const toggleTracking = document.getElementById('toggle-tracking');
    const trackingStatusText = document.getElementById('tracking-status-text');
    const metricSent = document.getElementById('metric-sent');
    const metricBuffered = document.getElementById('metric-buffered');
    const btnReconnect = document.getElementById('btn-reconnect');
    const eventsList = document.getElementById('events-list');

    function updateStatus() {
        if (!api || !api.runtime || !api.runtime.sendMessage) return;

        api.runtime.sendMessage({ type: 'GET_SENSOR_STATUS' }, (res) => {
            if (!res) {
                setConnState('offline', 'Offline');
                return;
            }

            if (res.connected) {
                setConnState('online', 'Connected');
            } else {
                setConnState('offline', 'Disconnected');
            }

            metricSent.textContent = res.totalSent || 0;
            metricBuffered.textContent = res.bufferedCount || 0;

            toggleTracking.checked = !!res.isTrackingEnabled;
            trackingStatusText.textContent = res.isTrackingEnabled 
                ? 'Streaming events to Core Engine' 
                : 'Observation paused';

            renderRecentEvents(res.recentEvents || []);
        });
    }

    function setConnState(state, text) {
        connBadge.className = `status-badge ${state}`;
        connText.textContent = text;
    }

    function renderRecentEvents(events) {
        if (!events || events.length === 0) {
            eventsList.innerHTML = '<div class="empty-events">Listening for browser events...</div>';
            return;
        }

        eventsList.innerHTML = '';
        events.forEach(ev => {
            const entry = document.createElement('div');
            entry.className = 'event-entry';

            let detail = '';
            const p = ev.payload || {};
            if (ev.event_type === 'search_performed') {
                detail = `🔍 "${p.query || ''}"`;
            } else if (ev.event_type === 'youtube_watching') {
                detail = `🎬 ${p.video_title || 'Video'}`;
            } else if (ev.event_type === 'bookmark_added') {
                detail = `🔖 ${p.title || p.url || ''}`;
            } else {
                detail = p.title || p.url || '';
            }

            entry.innerHTML = `
                <span class="event-type-badge">${ev.event_type}</span>
                <span class="event-detail" title="${escapeHtml(detail)}">${escapeHtml(detail)}</span>
            `;
            eventsList.appendChild(entry);
        });
    }

    // Toggle Tracking
    toggleTracking.addEventListener('change', () => {
        api.runtime.sendMessage({ type: 'TOGGLE_TRACKING' }, (res) => {
            if (res) {
                trackingStatusText.textContent = res.isTrackingEnabled 
                    ? 'Streaming events to Core Engine' 
                    : 'Observation paused';
            }
        });
    });

    // Reconnect Button
    btnReconnect.addEventListener('click', () => {
        setConnState('reconnecting', 'Connecting...');
        api.runtime.sendMessage({ type: 'RECONNECT_WS' }, () => {
            setTimeout(updateStatus, 1000);
        });
    });

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    document.addEventListener('DOMContentLoaded', () => {
        updateStatus();
        setInterval(updateStatus, 1500);
    });
})();
