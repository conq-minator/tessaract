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
        return this.fetchJSON('/api/context', {}, 1000); // 1s cache
    },

    async getFriction() {
        return this.fetchJSON('/api/friction', {}, 1000); // 1s cache
    },

    async getEpisodes() {
        return this.fetchJSON('/api/episodes', {}, 1000); // 1s cache
    },

    async getSession() {
        return this.fetchJSON('/api/session', {}, 1000); // 1s cache
    },

    async getAnalytics() {
        return this.fetchJSON('/api/analytics', {}, 1000);
    },

    async getKnowledgeGraph() {
        return this.fetchJSON('/api/knowledge-graph', {}, 500); // 0.5s cache for instant updates
    },

    async getRecommendations() {
        return this.fetchJSON('/api/recommendations', {}, 2000); // 2s cache
    },

    async getModels() {
        const resp = await fetch('/api/models');
        return await resp.json();
    },

    async selectModel(modelName) {
        const resp = await fetch('/api/models/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_name: modelName })
        });
        return await resp.json();
    },

    async deleteAllData() {
        this.invalidateCache();
        const resp = await fetch('/api/data/all', {
            method: 'DELETE'
        });
        return await resp.json();
    },

    async getBrowserInterests() {
        return this.fetchJSON('/api/browser-interests', {}, 1000);
    },

    async getBrowserActivity() {
        return this.fetchJSON('/api/browser-activity', {}, 1000);
    },

    async generateRoadmap(interestId, topic, standing) {
        this.invalidateCache();
        const resp = await fetch('/api/roadmap/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ interest_id: interestId, topic: topic, standing: standing })
        });
        return await resp.json();
    },

    async deleteRoadmap(interestId) {
        this.invalidateCache();
        const resp = await fetch(`/api/roadmap/${encodeURIComponent(interestId)}`, {
            method: 'DELETE'
        });
        return await resp.json();
    },

    invalidateCache() {
        _apiCache.clear();
    }
};

window.API = API;

