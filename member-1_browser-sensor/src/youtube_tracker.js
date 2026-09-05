/**
 * Tesseract Browser Sensor — YouTube Metadata and Watch-Time Tracker.
 * Extracts video title, channel, description, and watch duration to send to Core Engine.
 */

(function() {
  'use strict';

  function extractYouTubeMetadata() {
    // 1. Video Title
    const titleElement = 
      document.querySelector('h1.ytd-watch-metadata yt-formatted-string') ||
      document.querySelector('#title h1 yt-formatted-string') ||
      document.querySelector('meta[name="title"]');
    
    const title = (titleElement?.innerText || titleElement?.content || document.title || '')
      .replace(/\s*-\s*YouTube\s*$/i, '')
      .trim();

    // 2. Channel Name
    const channelElement =
      document.querySelector('#owner #channel-name #text a') ||
      document.querySelector('#channel-name #text') ||
      document.querySelector('ytd-channel-name yt-formatted-string');
    
    const channel = (channelElement?.innerText || '').trim();

    // 3. Short description / snippet
    const descElement =
      document.querySelector('#description-inline-expander') ||
      document.querySelector('#description yt-formatted-string') ||
      document.querySelector('meta[name="description"]');
    
    const description = (descElement?.innerText || descElement?.content || '').slice(0, 400).trim();

    // 4. Video duration and current time
    const video = document.querySelector('video');
    const duration_s = video ? Math.round(video.duration || 0) : 0;
    const current_time_s = video ? Math.round(video.currentTime || 0) : 0;

    return {
      url: window.location.href,
      title: title,
      video_title: title,
      channel: channel,
      description: description,
      duration_s: duration_s,
      watch_time_s: current_time_s,
      timestamp: new Date().toISOString()
    };
  }

  // Export for WebExtension background / content script integration
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { extractYouTubeMetadata };
  } else {
    window.__tesseractYouTubeMetadata = extractYouTubeMetadata;
  }
})();
