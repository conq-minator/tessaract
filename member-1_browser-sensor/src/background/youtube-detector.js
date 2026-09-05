/**
 * YouTube Educational Video Watching Detector & Duration Tracker
 */

class YouTubeDetector {
    constructor(eventEmitter) {
        this.emit = eventEmitter;
        this.activeVideos = new Map(); // videoId -> { startTime, lastEmitted, title, channel, duration }
    }

    init() {
        const api = globalThis.browser || globalThis.chrome;
        if (!api) return;

        // Listen for messages from YouTube content script
        if (api.runtime && api.runtime.onMessage) {
            api.runtime.onMessage.addListener((message, sender, sendResponse) => {
                if (message && message.type === 'YOUTUBE_STATUS_UPDATE') {
                    this._handleYouTubeStatusUpdate(message.payload);
                }
            });
        }

        // Tab URL monitoring fallback
        if (api.tabs) {
            api.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
                if (tab && tab.url && tab.url.includes('youtube.com/watch')) {
                    this._checkVideoFromTab(tab);
                }
            });
        }

        // Periodic check to emit watching progress
        setInterval(() => {
            this._flushActiveWatches();
        }, 15000); // every 15s
    }

    _handleYouTubeStatusUpdate(data) {
        if (!data || !data.video_url) return;

        const videoId = this._extractVideoId(data.video_url);
        if (!videoId) return;

        const now = Date.now();
        if (!this.activeVideos.has(videoId)) {
            this.activeVideos.set(videoId, {
                startTime: now,
                lastEmitted: 0,
                video_url: data.video_url,
                video_title: data.video_title || 'YouTube Video',
                channel: data.channel || 'YouTube Creator',
                duration_s: data.duration_s || 0,
                watch_time_s: 0
            });
        }

        const record = this.activeVideos.get(videoId);
        if (data.video_title) record.video_title = data.video_title;
        if (data.channel) record.channel = data.channel;
        if (data.duration_s) record.duration_s = data.duration_s;
        if (data.current_time_s) record.watch_time_s = Math.max(record.watch_time_s, Math.round(data.current_time_s));

        // Emit if new or enough time elapsed
        if (now - record.lastEmitted > 10000) {
            record.lastEmitted = now;
            this.emit('youtube_watching', {
                video_url: record.video_url,
                video_title: record.video_title,
                channel: record.channel,
                duration_s: record.duration_s,
                watch_time_s: record.watch_time_s || Math.round((now - record.startTime) / 1000)
            });
        }
    }

    _checkVideoFromTab(tab) {
        const videoId = this._extractVideoId(tab.url);
        if (!videoId) return;

        const now = Date.now();
        if (!this.activeVideos.has(videoId)) {
            this.activeVideos.set(videoId, {
                startTime: now,
                lastEmitted: now,
                video_url: tab.url,
                video_title: (tab.title || '').replace(' - YouTube', '').trim() || 'YouTube Video',
                channel: 'YouTube Creator',
                duration_s: 0,
                watch_time_s: 30
            });

            this.emit('youtube_watching', {
                video_url: tab.url,
                video_title: (tab.title || '').replace(' - YouTube', '').trim() || 'YouTube Video',
                channel: 'YouTube Creator',
                duration_s: 0,
                watch_time_s: 30
            });
        }
    }

    _flushActiveWatches() {
        const now = Date.now();
        for (const [videoId, record] of this.activeVideos.entries()) {
            // If active within last 2 minutes
            if (now - record.lastEmitted < 120000 && now - record.lastEmitted > 20000) {
                record.lastEmitted = now;
                const elapsed = Math.round((now - record.startTime) / 1000);
                this.emit('youtube_watching', {
                    video_url: record.video_url,
                    video_title: record.video_title,
                    channel: record.channel,
                    duration_s: record.duration_s,
                    watch_time_s: Math.max(record.watch_time_s, elapsed)
                });
            }
        }
    }

    _extractVideoId(url) {
        try {
            const u = new URL(url);
            return u.searchParams.get('v') || u.pathname.split('/').pop();
        } catch (e) {
            return null;
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { YouTubeDetector };
}
