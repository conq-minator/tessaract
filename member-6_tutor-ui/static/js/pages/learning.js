/**
 * Tesseract AI Learning Roadmap Page Logic
 * Dynamically populated from real browser interests & code mastery models
 */

(function () {
    let allInterests = [];
    let selectedInterestId = null;
    let lastRenderedHash = "";

    function init() {
        loadDynamicRoadmaps();
        setInterval(loadDynamicRoadmaps, 8000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.refreshLearning = async function (force = false) {
        if (force) {
            window.API.invalidateCache();
            lastRenderedHash = "";
        }
        await loadDynamicRoadmaps();
        if (window.Notifications) {
            window.Notifications.info('Roadmap Synced', 'Updated from active telemetry and AI models.');
        }
    };

    async function loadDynamicRoadmaps() {
        try {
            const data = await window.API.getBrowserInterests();
            const interests = (data && Array.isArray(data.interests)) ? data.interests : [];
            allInterests = interests;

            const currentHash = JSON.stringify(interests);
            if (currentHash === lastRenderedHash && selectedInterestId) {
                return; // Nothing changed, avoid re-rendering to prevent any flicker
            }
            lastRenderedHash = currentHash;

            renderTopicTabs(interests);

            if (interests.length > 0) {
                if (!selectedInterestId || !interests.some(i => i.id === selectedInterestId)) {
                    selectedInterestId = interests[0].id;
                }
                const activeInterest = interests.find(i => i.id === selectedInterestId) || interests[0];
                renderRoadmap(activeInterest);
                renderRecommendations(activeInterest);
            } else {
                renderEmptyRoadmapState();
            }
        } catch (e) {
            console.error("Failed to load learning data:", e);
        }
    }

    function renderTopicTabs(interests) {
        const bar = document.getElementById('roadmap-topics-bar');
        if (!bar) return;

        bar.innerHTML = '';
        if (interests.length === 0) {
            bar.style.display = 'none';
            return;
        }

        bar.style.display = 'flex';
        interests.forEach(item => {
            const btn = document.createElement('button');
            btn.className = `roadmap-topic-tab ${item.id === selectedInterestId ? 'active' : ''}`;
            btn.onclick = () => {
                selectedInterestId = item.id;
                document.querySelectorAll('.roadmap-topic-tab').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderRoadmap(item);
                renderRecommendations(item);
            };

            btn.innerHTML = `
                <span>${item.icon || '💡'}</span>
                <span>${escapeHtml(item.title)}</span>
                <span class="badge badge-sm" style="font-size: 0.7rem; color: ${item.standing_color}; border-color: ${item.standing_color};">${item.standing}</span>
            `;
            bar.appendChild(btn);
        });
    }

    function renderRoadmap(data) {
        const subjectEl = document.getElementById('rm-subject');
        const descEl = document.getElementById('rm-desc');
        const iconEl = document.getElementById('rm-icon');
        const levelEl = document.getElementById('rm-level');
        const nextMilestoneEl = document.getElementById('rm-next-milestone');
        const statusBadge = document.getElementById('rm-status-badge');
        const timeline = document.getElementById('rm-timeline');

        if (subjectEl) subjectEl.textContent = data.title;
        if (descEl) descEl.textContent = `Adaptive curriculum based on ${data.stats?.watch_time_minutes || 0}m YouTube study and ${data.stats?.searches_count || 0} searches.`;
        if (iconEl) iconEl.textContent = data.icon || '🚀';
        if (levelEl) {
            levelEl.textContent = `${data.standing} (${data.standing_score || 50}%)`;
            levelEl.style.color = data.standing_color || '#f59e0b';
        }
        if (nextMilestoneEl) nextMilestoneEl.textContent = data.next_milestone || "Continue structured video progression";
        if (statusBadge) {
            statusBadge.textContent = data.standing_badge || "🟡 In Progress";
            statusBadge.style.color = data.standing_color || '#f59e0b';
        }

        if (!timeline) return;
        timeline.innerHTML = '';

        const roadmapItems = data.roadmap || [];
        if (roadmapItems.length === 0) {
            timeline.innerHTML = '<div class="text-muted" style="padding: 20px;">No milestones mapped yet.</div>';
            return;
        }

        roadmapItems.forEach((ms, idx) => {
            const isCompleted = ms.completed;
            const statusClass = isCompleted ? 'completed' : idx === 0 ? 'active' : 'pending';
            const statusLabel = isCompleted ? 'COMPLETED' : idx === 0 ? 'IN PROGRESS' : 'RECOMMENDED';

            const msEl = document.createElement('div');
            msEl.className = `milestone ${statusClass}`;
            msEl.innerHTML = `
                <div class="ms-title">Phase ${idx + 1}: ${escapeHtml(ms.title)}</div>
                <div class="ms-meta">
                    Level: ${escapeHtml(ms.level || 'Foundational')} &bull; Est: ${escapeHtml(ms.duration || '30 min')} &bull; Status: <strong style="color: ${isCompleted ? '#10b981' : '#6366f1'};">${statusLabel}</strong>
                </div>
                <a href="${escapeHtml(ms.url)}" target="_blank" rel="noopener noreferrer" class="ms-video-link">
                    <span>🎬 Watch Milestone Tutorial (${escapeHtml(ms.channel || 'YouTube')})</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                </a>
            `;
            timeline.appendChild(msEl);
        });
    }

    function renderRecommendations(interest) {
        const list = document.getElementById('rec-list');
        if (!list) return;
        list.innerHTML = '';

        const videos = (interest && interest.recent_videos) ? interest.recent_videos : [];
        const roadmapItems = (interest && interest.roadmap) ? interest.roadmap : [];

        const allRecs = [];
        videos.forEach(v => {
            allRecs.push({
                title: v.title,
                channel: v.channel,
                duration: `${Math.round(v.watch_time_s / 60)}m watched`,
                url: v.url
            });
        });
        roadmapItems.forEach(r => {
            if (!allRecs.some(x => x.title === r.title)) {
                allRecs.push({
                    title: r.title,
                    channel: r.channel,
                    duration: r.duration,
                    url: r.url
                });
            }
        });

        if (allRecs.length === 0) {
            list.innerHTML = '<div class="text-muted" style="padding: 20px;">No video resources found.</div>';
            return;
        }

        allRecs.slice(0, 5).forEach(rec => {
            const item = document.createElement('a');
            item.href = rec.url;
            item.target = '_blank';
            item.rel = 'noopener noreferrer';
            item.className = 'rec-item';
            item.innerHTML = `
                <div class="rec-title">${escapeHtml(rec.title)}</div>
                <div class="rec-meta">
                    <span class="badge badge-primary">🎬 ${escapeHtml(rec.channel)}</span>
                    <span>${escapeHtml(rec.duration)}</span>
                </div>
            `;
            list.appendChild(item);
        });
    }

    function renderEmptyRoadmapState() {
        const subjectEl = document.getElementById('rm-subject');
        const descEl = document.getElementById('rm-desc');
        const timeline = document.getElementById('rm-timeline');
        const recList = document.getElementById('rec-list');

        if (subjectEl) subjectEl.textContent = "No Roadmaps Generated Yet";
        if (descEl) descEl.textContent = "Browse technical documentation or watch YouTube tutorials with the Tesseract Browser Sensor active.";
        if (timeline) {
            timeline.innerHTML = `
                <div style="padding: 40px 20px; text-align: center; color: var(--text-tertiary);">
                    <div style="font-size: 2rem; margin-bottom: 12px;">🗺️</div>
                    <div style="font-size: 1.05rem; font-weight: 600; color: #f8fafc; margin-bottom: 6px;">Zero Learning Telemetry Detected</div>
                    <div style="font-size: 0.85rem; max-width: 440px; margin: 0 auto; line-height: 1.5;">
                        As you search developer queries on Google/Bing or watch tutorials on YouTube, SmolLM will automatically extract your learning objectives and build step-by-step video roadmaps here.
                    </div>
                </div>
            `;
        }
        if (recList) {
            recList.innerHTML = '<div class="text-muted" style="padding: 20px; text-align: center;">Waiting for active learning sessions...</div>';
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
})();
