/**
 * Tesseract Browser Sensor - Cross-Browser API Polyfill
 * Normalizes 'browser' vs 'chrome' namespace across Firefox, Brave, Chrome, and Edge.
 */

(function () {
    if (typeof globalThis.browser === 'undefined') {
        globalThis.browser = globalThis.chrome;
    }
})();
