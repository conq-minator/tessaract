/**
 * YouTube Content Script
 * Injected on YouTube video pages to extract video title, channel name, duration, and watching progress.
 */

(function () {
    const api = globalThis.browser || globalThis.chrome;
    let lastUrl = location.href;
    let pollTimer = null;

    function extractYouTubeMeta() {
        if (!location.pathname.startsWith('/watch')) return null;

        const videoEl = document.querySelector('video.html5-main-video');
        const titleEl = document.querySelector('h1.ytd-watch-metadata yt-formatted-string') || document.querySelector('h1.title yt-formatted-string') || document.querySelector('h1.title');
        const channelEl = document.querySelector('ytd-channel-name a') || document.querySelector('#owner #channel-name a') || document.querySelector('#upload-info ytd-channel-name a');

        const title = titleEl ? titleEl.textContent.trim() : document.title.replace(' - YouTube', '').trim();
        const channel = channelEl ? channelEl.textContent.trim() : 'YouTube Channel';
        const duration = videoEl ? Math.round(videoEl.duration || 0) : 0;
        const currentTime = videoEl ? Math.round(videoEl.currentTime || 0) : 0;
        const isPaused = videoEl ? videoEl.paused : false;

        return {
            video_url: location.href,
            video_title: title,
            channel: channel,
            duration_s: duration,
            current_time_s: currentTime,
            is_paused: isPaused
        };
    }

    function sendUpdate() {
        const meta = extractYouTubeMeta();
        if (meta && api && api.runtime && api.runtime.sendMessage) {
            try {
                api.runtime.sendMessage({
                    type: 'YOUTUBE_STATUS_UPDATE',
                    payload: meta
                });
            } catch (e) {}
        }
    }

    // Start periodic observation
    function startObserving() {
        if (pollTimer) clearInterval(pollTimer);
        sendUpdate();
        pollTimer = setInterval(() => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                sendUpdate();
            } else {
                const videoEl = document.querySelector('video.html5-main-video');
                if (videoEl && !videoEl.paused) {
                    sendUpdate();
                }
            }
        }, 10000); // Check every 10 seconds
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        startObserving();
    } else {
        window.addEventListener('DOMContentLoaded', startObserving);
    }
})();
