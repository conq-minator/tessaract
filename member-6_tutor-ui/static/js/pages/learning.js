/**
 * Tesseract AI Learning Roadmap & Discovered Interests Page Logic
 * Features on-demand dynamic curriculum generation with verified tutorial resources.
 * Pure monochrome theme (ChatGPT / Ollama design language).
 */

(function () {
    let allInterests = [];
    let selectedInterestId = null;
    let lastRenderedHash = "";
    let isGenerating = false;

    function init() {
        loadDynamicRoadmaps();
        setInterval(() => {
            if (!isGenerating) {
                loadDynamicRoadmaps();
            }
        }, 10000);
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
            window.Notifications.info('Learning Synced', 'Updated from telemetry and curriculum store.');
        }
    };

    window.activateRoadmap = async function (interestId, topic, standing) {
        if (isGenerating) return;
        isGenerating = true;

        const btn = document.getElementById(`btn-activate-${interestId}`) || document.querySelector('.btn-activate-roadmap');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin-animation" style="animation: spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle><path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="0.85"></path></svg>
                <span>Synthesizing Multi-Phase Curriculum...</span>
            `;
        }

        try {
            const res = await window.API.generateRoadmap(interestId, topic, standing);
            if (res && res.status === 'success') {
                if (window.Notifications) {
                    window.Notifications.success('Curriculum Synthesized', `${res.phases_count || 6}-phase structured roadmap for ${topic} created.`);
                }
            } else {
                if (window.Notifications) {
                    window.Notifications.error('Generation Notice', res.message || 'Could not generate curriculum.');
                }
            }
        } catch (e) {
            console.error("Failed to generate roadmap:", e);
            if (window.Notifications) {
                window.Notifications.error('Generation Failed', String(e));
            }
        } finally {
            isGenerating = false;
            window.API.invalidateCache();
            lastRenderedHash = "";
            await loadDynamicRoadmaps();
        }
    };

    window.resetRoadmap = async function (interestId) {
        if (!confirm("Remove active roadmap and revert to Discovered Interest?")) return;
        try {
            await window.API.deleteRoadmap(interestId);
            window.API.invalidateCache();
            lastRenderedHash = "";
            await loadDynamicRoadmaps();
            if (window.Notifications) {
                window.Notifications.info('Roadmap Reverted', 'Returned to discovered interest state.');
            }
        } catch (e) {
            console.error("Failed to delete roadmap:", e);
        }
    };

    async function loadDynamicRoadmaps() {
        try {
            const res = await window.API.getBrowserInterests();
            const data = (res && res.data) ? res.data : (res || {});
            const interests = (data && Array.isArray(data.interests)) ? data.interests : [];
            allInterests = interests;

            // Render Engine Status Pill
            renderCloudPill(data.cloud_status);

            const currentHash = JSON.stringify({ interests, cloud: data.cloud_status });
            if (currentHash === lastRenderedHash && selectedInterestId) {
                return;
            }
            lastRenderedHash = currentHash;

            renderTopicTabs(interests);

            if (interests.length > 0) {
                if (!selectedInterestId || !interests.some(i => i.id === selectedInterestId)) {
                    selectedInterestId = interests[0].id;
                }
                const activeInterest = interests.find(i => i.id === selectedInterestId) || interests[0];
                renderInterestView(activeInterest);
                renderRecommendations(activeInterest);
            } else {
                renderEmptyRoadmapState();
            }
        } catch (e) {
            console.error("Failed to load learning data:", e);
        }
    }

    function renderCloudPill(cloudStatus) {
        const label = document.getElementById('ai-engine-label');
        const pill = document.getElementById('ai-cloud-pill');
        if (!label || !pill) return;

        if (cloudStatus && cloudStatus.enabled) {
            label.textContent = (cloudStatus.description || 'GEMINI FLASH (CLOUD)').toUpperCase();
            pill.style.background = '#18181b';
            pill.style.borderColor = '#3f3f46';
            pill.style.color = '#ffffff';
        } else {
            label.textContent = 'LOCAL ENGINE • OFFLINE';
            pill.style.background = '#18181b';
            pill.style.borderColor = '#27272a';
            pill.style.color = '#a1a1aa';
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
            const isActive = item.id === selectedInterestId;
            btn.className = `roadmap-topic-tab ${isActive ? 'active' : ''}`;
            btn.onclick = () => {
                selectedInterestId = item.id;
                document.querySelectorAll('.roadmap-topic-tab').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderInterestView(item);
                renderRecommendations(item);
            };

            const tag = (item.icon && !isEmoji(item.icon)) ? item.icon : (item.title ? item.title.slice(0, 3).toUpperCase() : 'DEV');
            const statusTag = item.has_roadmap
                ? '<span class="mono-badge">[ACTIVE]</span>'
                : '<span class="mono-badge mono-badge-subtle">[DISCOVERED]</span>';

            btn.innerHTML = `
                <span class="mono-badge">[${escapeHtml(tag)}]</span>
                <span>${escapeHtml(item.title)}</span>
                <span class="mono-badge mono-badge-subtle">${escapeHtml(item.standing.toUpperCase())}</span>
                ${statusTag}
            `;
            bar.appendChild(btn);
        });
    }

    function renderInterestView(data) {
        const subjectEl = document.getElementById('rm-subject');
        const descEl = document.getElementById('rm-desc');
        const levelEl = document.getElementById('rm-level');
        const nextMilestoneEl = document.getElementById('rm-next-milestone');
        const statusBadge = document.getElementById('rm-status-badge');
        const actionBtns = document.getElementById('rm-action-btns');
        const timeline = document.getElementById('rm-timeline');
        const cardTitle = document.getElementById('rm-card-title');

        if (subjectEl) subjectEl.textContent = data.title;
        if (levelEl) {
            levelEl.textContent = `[${data.standing.toUpperCase()}] ${data.standing_score || 50}%`;
        }
        if (nextMilestoneEl) nextMilestoneEl.textContent = data.next_milestone || "Continue progressive sequence";

        if (data.has_roadmap && data.roadmap && data.roadmap.length > 0) {
            // State A: Active Comprehensive Multi-Phase Roadmap
            if (cardTitle) cardTitle.textContent = "Multi-Phase Curriculum Roadmap";
            if (descEl) descEl.textContent = `Structured sequence (${data.roadmap.length} phases) generated for ${data.title}.`;
            if (statusBadge) {
                statusBadge.textContent = "[ROADMAP ACTIVE]";
                statusBadge.className = "mono-badge";
            }

            if (actionBtns) {
                actionBtns.innerHTML = `
                    <button class="btn btn-secondary btn-sm" title="Regenerate Curriculum" onclick="window.activateRoadmap('${data.id}', '${escapeHtml(data.title)}', '${data.standing}')">
                        Regenerate
                    </button>
                    <button class="btn btn-secondary btn-sm" title="Revert to Discovered Interest" onclick="window.resetRoadmap('${data.id}')">
                        Reset
                    </button>
                `;
            }

            if (!timeline) return;
            timeline.innerHTML = '';

            data.roadmap.forEach((ms, idx) => {
                const isCompleted = Boolean(ms.completed);
                const statusClass = isCompleted ? 'completed' : idx === 0 ? 'active' : 'pending';
                const statusLabel = isCompleted ? '[COMPLETED]' : idx === 0 ? '[CURRENT]' : '[UPCOMING]';

                const msEl = document.createElement('div');
                msEl.className = `milestone ${statusClass}`;
                msEl.innerHTML = `
                    <span class="ms-phase-tag">PHASE ${ms.phase || idx + 1} &bull; ${escapeHtml(ms.level || 'INTERMEDIATE').toUpperCase()}</span>
                    <div class="ms-title">${escapeHtml(ms.title)}</div>
                    ${ms.description ? `<div class="ms-desc">${escapeHtml(ms.description)}</div>` : ''}
                    <div class="ms-meta">
                        <span>Duration: <strong>${escapeHtml(ms.duration || '2h 00m')}</strong></span>
                        &bull;
                        <span>Channel: <strong>${escapeHtml(ms.channel || 'Tutorial')}</strong></span>
                        &bull;
                        <span>Status: <strong>${statusLabel}</strong></span>
                    </div>
                    <div class="ms-actions-row">
                        <a href="${escapeHtml(ms.url)}" target="_blank" rel="noopener noreferrer" class="ms-video-link">
                            <span>Open Tutorial (${escapeHtml(ms.channel || 'Resource')})</span>
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                        </a>
                    </div>
                `;
                timeline.appendChild(msEl);
            });
        } else {
            // State B: Discovered Interest (Prompt user to click "I'm interested" to generate roadmap)
            if (cardTitle) cardTitle.textContent = "Discovered Learning Interest";
            if (descEl) descEl.textContent = `Identified from ${data.stats?.watch_time_minutes || 0}m telemetry and ${data.stats?.searches_count || 0} searches.`;
            if (statusBadge) {
                statusBadge.textContent = "[DISCOVERED]";
                statusBadge.className = "mono-badge mono-badge-subtle";
            }

            if (actionBtns) actionBtns.innerHTML = '';

            if (!timeline) return;
            timeline.innerHTML = `
                <div class="interest-activation-card animate-fade-in">
                    <span class="activation-tag">[TOPIC DISCOVERED]</span>
                    <h3 class="activation-title">${escapeHtml(data.title)}</h3>
                    <p class="activation-desc">
                        Tesseract observed active development and research in <strong>${escapeHtml(data.title)}</strong> (${data.stats?.videos_watched || 0} videos, ${data.stats?.searches_count || 0} queries).
                        <br><br>
                        Click below to synthesize a dynamic, <strong>multi-phase roadmap (5–7 progressive phases)</strong> from foundation to advanced engineering.
                    </p>
                    <button id="btn-activate-${data.id}" class="btn-activate-roadmap" onclick="window.activateRoadmap('${data.id}', '${escapeHtml(data.title)}', '${data.standing}')">
                        Synthesize Comprehensive Roadmap
                    </button>
                </div>
            `;
        }
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
                duration: `${Math.round(v.watch_time_s / 60)}m`,
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
            list.innerHTML = '<div class="text-muted" style="padding: 20px; font-size: 0.85rem; color: #71717a;">No resources recorded yet.</div>';
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
                    <span class="mono-badge mono-badge-subtle">[${escapeHtml(rec.channel || 'SOURCE')}]</span>
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

        if (subjectEl) subjectEl.textContent = "No Discovered Interests";
        if (descEl) descEl.textContent = "Telemetry will register technical searches and documentation sessions automatically.";
        if (timeline) {
            timeline.innerHTML = `
                <div style="padding: 40px 20px; text-align: center; color: #71717a;">
                    <div style="font-family: monospace; font-size: 0.9rem; color: #ffffff; margin-bottom: 8px;">[TELEMETRY STANDBY]</div>
                    <div style="font-size: 0.85rem; max-width: 440px; margin: 0 auto; line-height: 1.5; color: #a1a1aa;">
                        As you search programming topics or study documentation, Tesseract will extract topics and build progressive curricula here.
                    </div>
                </div>
            `;
        }
        if (recList) {
            recList.innerHTML = '<div class="text-muted" style="padding: 20px; text-align: center; font-size: 0.85rem; color: #71717a;">Standing by for study sessions...</div>';
        }
    }

    function isEmoji(str) {
        if (!str) return false;
        return /[\u{1F300}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u.test(str);
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
})();
