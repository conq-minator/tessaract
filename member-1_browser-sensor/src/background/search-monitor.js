/**
 * Search Engine Query Monitor
 * Intercepts search queries from Google, Bing, DuckDuckGo, YouTube, GitHub, StackOverflow, Yahoo, and Baidu.
 */

class SearchMonitor {
    constructor(eventEmitter) {
        this.emit = eventEmitter;
        this.lastSearches = new Set(); // Prevent duplicate rapid emissions
    }

    init() {
        const api = globalThis.browser || globalThis.chrome;
        if (!api || !api.tabs) return;

        api.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.url || (changeInfo.status === 'complete' && tab && tab.url)) {
                this.checkUrlForSearch(tab.url || changeInfo.url);
            }
        });
    }

    checkUrlForSearch(urlString) {
        if (!urlString) return;

        try {
            const url = new URL(urlString);
            const host = url.hostname.toLowerCase();
            let query = null;
            let engine = null;

            // Google
            if (host.includes('google.') && (url.pathname === '/search' || url.pathname === '/webhp')) {
                query = url.searchParams.get('q');
                engine = 'Google';
            }
            // Bing
            else if (host.includes('bing.com') && url.pathname === '/search') {
                query = url.searchParams.get('q');
                engine = 'Bing';
            }
            // DuckDuckGo
            else if (host.includes('duckduckgo.com') && (url.pathname === '/' || url.pathname === '/html/')) {
                query = url.searchParams.get('q');
                engine = 'DuckDuckGo';
            }
            // YouTube Search
            else if (host.includes('youtube.com') && url.pathname === '/results') {
                query = url.searchParams.get('search_query');
                engine = 'YouTube';
            }
            // GitHub Search
            else if (host.includes('github.com') && url.pathname === '/search') {
                query = url.searchParams.get('q');
                engine = 'GitHub';
            }
            // StackOverflow Search
            else if (host.includes('stackoverflow.com') && url.pathname === '/search') {
                query = url.searchParams.get('q');
                engine = 'StackOverflow';
            }
            // Yahoo Search
            else if (host.includes('search.yahoo.com') && url.pathname.includes('/search')) {
                query = url.searchParams.get('p');
                engine = 'Yahoo';
            }
            // Baidu Search
            else if (host.includes('baidu.com') && url.pathname === '/s') {
                query = url.searchParams.get('wd') || url.searchParams.get('word');
                engine = 'Baidu';
            }

            if (query && query.trim().length > 0) {
                const cleanQuery = query.trim();
                const dedupKey = `${engine}:${cleanQuery.toLowerCase()}`;

                if (!this.lastSearches.has(dedupKey)) {
                    this.lastSearches.add(dedupKey);
                    // Keep dedup set small
                    if (this.lastSearches.size > 50) {
                        const first = this.lastSearches.values().next().value;
                        this.lastSearches.delete(first);
                    }

                    this.emit('search_performed', {
                        query: cleanQuery,
                        engine: engine,
                        url: urlString
                    });
                }
            }
        } catch (e) {}
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SearchMonitor };
}
