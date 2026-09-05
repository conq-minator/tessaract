/**
 * Bookmark Creation Tracker
 */

class BookmarkTracker {
    constructor(eventEmitter) {
        this.emit = eventEmitter;
    }

    init() {
        const api = globalThis.browser || globalThis.chrome;
        if (!api || !api.bookmarks) return;

        api.bookmarks.onCreated.addListener((id, bookmark) => {
            if (bookmark && bookmark.url) {
                this.emit('bookmark_added', {
                    bookmark_id: id,
                    url: bookmark.url,
                    title: bookmark.title || ''
                });
            }
        });
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BookmarkTracker };
}
