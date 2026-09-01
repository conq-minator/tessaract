/**
 * api.js - Centralized fetch wrapper for the Tesseract UI
 */

const API = {
    async fetchJSON(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            if (data.status !== "success" && data.status !== "ok") {
                throw new Error(`API Error: ${data.message || 'Unknown error'}`);
            }
            return data.data;
        } catch (error) {
            console.error(`[API] Failed to fetch ${endpoint}:`, error);
            // Re-throw to let components handle their own UI error states
            throw error;
        }
    },

    async getContext() {
        return this.fetchJSON('/api/context');
    },

    async getFriction() {
        return this.fetchJSON('/api/friction');
    },

    async getEpisodes() {
        return this.fetchJSON('/api/episodes');
    },

    async getSession() {
        return this.fetchJSON('/api/session');
    },

    async getAnalytics() {
        return this.fetchJSON('/api/analytics');
    },

    async getKnowledgeGraph() {
        return this.fetchJSON('/api/knowledge-graph');
    },

    async getRecommendations() {
        return this.fetchJSON('/api/recommendations');
    }
};

window.API = API;
