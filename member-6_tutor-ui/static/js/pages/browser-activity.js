/**
 * Browser Activity Telemetry Dashboard JS
 */

(function () {
    let lastSignature = '';

    document.addEventListener('DOMContentLoaded', async () => {
        await loadBrowserActivity();
        setInterval(loadBrowserActivity, 3000);
    });

    window.refreshBrowserActivity = async function (force = false) {
        if (force) {
            window.API.invalidateCache();
        }
        await loadBrowserActivity();
        if (window.Notifications) {
            window.Notifications.info('Telemetry Updated', 'Browser activity synchronised from sensor feed.');
        }
    };

    async function loadBrowserActivity() {
        try {
            const data = await window.API.getBrowserActivity();
            if (!data) return;

            const currentSignature = JSON.stringify(data);
            if (currentSignature === lastSignature) return;
            lastSignature = currentSignature;

            renderActivity(data);
        } catch (err) {
            console.debug("Failed to load browser activity:", err);
        }
    }

    function renderActivity(data) {
        const {
            total_browser_events = 0,
            top_domains = [],
            recent_searches = [],
            youtube_videos = [],
            total_watch_minutes = 0
        } = data;

        // Banner Stats
        const statEvents = document.getElementById('stat-total-events');
        const statWatchMin = document.getElementById('stat-watch-minutes');
        const statSearches = document.getElementById('stat-searches-count');
        const statDomains = document.getElementById('stat-domains-count');

        if (statEvents) statEvents.textContent = total_browser_events;
        if (statWatchMin) statWatchMin.textContent = `${total_watch_minutes} min`;
        if (statSearches) statSearches.textContent = recent_searches.length;
        if (statDomains) statDomains.textContent = top_domains.length;

        // Top Domains
        const domainsList = document.getElementById('domains-list');
        if (domainsList) {
            domainsList.innerHTML = '';
            if (top_domains.length === 0) {
                domainsList.innerHTML = '<div class="empty-subtle">No domains recorded yet. Browse the web to generate telemetry.</div>';
            } else {
                top_domains.forEach(d => {
                    const item = document.createElement('div');
                    item.className = 'domain-item';
                    item.innerHTML = `
                        <span class="domain-name">🌐 ${escapeHtml(d.domain)}</span>
                        <span class="domain-count-badge">${d.count} hits</span>
                    `;
                    domainsList.appendChild(item);
                });
            }
        }

        // YouTube Log
        const youtubeLogList = document.getElementById('youtube-log-list');
        const youtubeSummary = document.getElementById('youtube-summary');
        if (youtubeSummary) youtubeSummary.textContent = `${youtube_videos.length} videos tracked`;
        if (youtubeLogList) {
            youtubeLogList.innerHTML = '';
            if (youtube_videos.length === 0) {
                youtubeLogList.innerHTML = '<div class="empty-subtle">No YouTube videos watched recently.</div>';
            } else {
                youtube_videos.forEach(yt => {
                    const item = document.createElement('div');
                    item.className = 'youtube-item';
                    const watchMin = Math.round((yt.watch_time_s || 0) / 60);
                    item.innerHTML = `
                        <div class="yt-left">
                            <span class="yt-icon">🎬</span>
                            <div>
                                <a href="${escapeHtml(yt.url)}" target="_blank" rel="noopener noreferrer" class="yt-title">
                                    ${escapeHtml(yt.title)}
                                </a>
                                <div class="yt-meta">
                                    <span>Channel: ${escapeHtml(yt.channel)}</span>
                                    <span>Duration: ${yt.duration_s ? yt.duration_s + 's' : 'N/A'}</span>
                                    <span>Watch Time: ~${watchMin} min</span>
                                </div>
                            </div>
                        </div>
                    `;
                    youtubeLogList.appendChild(item);
                });
            }
        }

        // Searches Log
        const searchesLogGrid = document.getElementById('searches-log-grid');
        const searchesSummary = document.getElementById('searches-summary');
        if (searchesSummary) searchesSummary.textContent = `${recent_searches.length} queries`;
        if (searchesLogGrid) {
            searchesLogGrid.innerHTML = '';
            if (recent_searches.length === 0) {
                searchesLogGrid.innerHTML = '<div class="empty-subtle" style="width: 100%;">No search queries detected yet.</div>';
            } else {
                recent_searches.forEach(s => {
                    const chip = document.createElement('div');
                    chip.className = 'search-log-item';
                    chip.innerHTML = `
                        <span>🔍</span>
                        <strong>${escapeHtml(s.query)}</strong>
                        <span class="text-muted" style="font-size: 0.75rem;">(${escapeHtml(s.engine || 'Search')})</span>
                    `;
                    searchesLogGrid.appendChild(chip);
                });
            }
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
})();
