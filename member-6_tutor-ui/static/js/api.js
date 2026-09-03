/**
 * api.js - Centralized fetch wrapper with in-memory caching for ultra-fast navigation
 */

const _apiCache = new Map();

const API = {
    async fetchJSON(endpoint, options = {}, ttlMs = 0) {
        const cacheKey = `${options.method || 'GET'}:${endpoint}`;
        
        // Return cached response if within TTL
        if (ttlMs > 0 && _apiCache.has(cacheKey)) {
            const cached = _apiCache.get(cacheKey);
            if (Date.now() - cached.timestamp < ttlMs) {
                return cached.data;
            }
        }

        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            if (data.status !== "success" && data.status !== "ok") {
                throw new Error(`API Error: ${data.message || 'Unknown error'}`);
            }
            
            if (ttlMs > 0) {
                _apiCache.set(cacheKey, { data: data.data, timestamp: Date.now() });
            }
            return data.data;
        } catch (error) {
            // If network fails but we have stale cache, fallback to cache
            if (_apiCache.has(cacheKey)) {
                return _apiCache.get(cacheKey).data;
            }
            console.error(`[API] Failed to fetch ${endpoint}:`, error);
            throw error;
        }
    },

    async getContext() {
        return this.fetchJSON('/api/context', {}, 2000); // 2s cache
    },

    async getFriction() {
        return this.fetchJSON('/api/friction', {}, 2000); // 2s cache
    },

    async getEpisodes() {
        return this.fetchJSON('/api/episodes', {}, 5000); // 5s cache
    },

    async getSession() {
        return this.fetchJSON('/api/session', {}, 5000); // 5s cache
    },

    async getAnalytics() {
        return this.fetchJSON('/api/analytics', {}, 10000);
    },

    async getKnowledgeGraph() {
        return this.fetchJSON('/api/knowledge-graph', {}, 30000); // 30s cache for fast graph rendering
    },

    async getRecommendations() {
        return this.fetchJSON('/api/recommendations', {}, 30000); // 30s cache
    },

    invalidateCache() {
        _apiCache.clear();
    }
};

window.API = API;
