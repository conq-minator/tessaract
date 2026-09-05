/**
 * Standardized TesseractEvent Formatter
 */

function generateUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function formatTesseractEvent(eventType, payload, metadata = {}) {
    return {
        event_id: generateUUID(),
        source: "browser",
        event_type: eventType,
        timestamp: new Date().toISOString(),
        payload: payload || {},
        metadata: {
            session_id: metadata.session_id || null,
            confidence: metadata.confidence || 1.0,
            privacy_level: metadata.privacy_level || "local_only",
            ...metadata
        }
    };
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { formatTesseractEvent, generateUUID };
}
