/**
 * Tesseract Topic & Subtopic Knowledge Mastery Dashboard + Browser Interests
 * 100% Dynamic Topic Mapping from Code Runs + Autonomous Browser Interests Roadmap
 */

(function () {
    const CIRCUMFERENCE = 251.2; // 2 * Math.PI * 40

    let currentMode = 'mastery'; // 'mastery' | 'interests'
    let dynamicCurriculum = {};  // Populated purely from backend knowledge nodes
    let activeTopicKey = null;
    let currentFilter = 'all';
    let currentInterestFilter = 'all';
    let currentSearchTerm = '';
    let selectedConceptData = null;
    let lastGraphSignature = '';
    let lastInterestsSignature = '';
    let cachedInterestsData = null;

    // DOM Elements - Mastery
    const viewCodeMastery = document.getElementById('view-code-mastery');
    const viewBrowserInterests = document.getElementById('view-browser-interests');
    const topicTabsBar = document.getElementById('topic-tabs');
    const topicBanner = document.getElementById('topic-banner');
    const bannerTitle = document.getElementById('banner-title');
    const bannerDesc = document.getElementById('banner-desc');
    const bannerIcon = document.getElementById('banner-icon');
    const bannerRadialPct = document.getElementById('banner-radial-pct');
    const bannerRingFill = document.getElementById('banner-ring-fill');
    const statSubtopics = document.getElementById('stat-subtopics-count');
    const statEpisodes = document.getElementById('stat-episodes-count');
    const statFriction = document.getElementById('stat-friction-rate');
    const sectionTitleRow = document.getElementById('section-title-row');
    const subtopicCountSummary = document.getElementById('subtopic-count-summary');
    const subtopicsGrid = document.getElementById('subtopics-grid');
    const masteryFilters = document.getElementById('mastery-filters');
    const interestsFilters = document.getElementById('interests-filters');

    // DOM Elements - Interests
    const interestsGrid = document.getElementById('interests-grid');
    const statInterestsCount = document.getElementById('stat-interests-count');
    const statTotalWatchTime = document.getElementById('stat-total-watch-time');
    const statBrowserEvents = document.getElementById('stat-browser-events');

    document.addEventListener('DOMContentLoaded', async () => {
        // Initial fetch from backend
        await fetchAndSyncLiveGraph();
        await fetchAndSyncInterests();

        // Polling sync every 3s (anti-flicker signature checked before touching DOM)
        setInterval(async () => {
            if (currentMode === 'mastery') {
                await fetchAndSyncLiveGraph();
            } else {
                await fetchAndSyncInterests();
            }
        }, 3000);
    });

    // ==========================================
    // VIEW MODE SWITCHER
    // ==========================================
    window.switchViewMode = function (mode) {
        currentMode = mode;
        const btnMastery = document.getElementById('btn-mode-mastery');
        const btnInterests = document.getElementById('btn-mode-interests');

        if (mode === 'mastery') {
            btnMastery.classList.add('active');
            btnInterests.classList.remove('active');
            viewCodeMastery.style.display = 'block';
            viewBrowserInterests.style.display = 'none';
            masteryFilters.style.display = 'flex';
            interestsFilters.style.display = 'none';
            renderMasteryView();
        } else {
            btnMastery.classList.remove('active');
            btnInterests.classList.add('active');
            viewCodeMastery.style.display = 'none';
            viewBrowserInterests.style.display = 'block';
            masteryFilters.style.display = 'none';
            interestsFilters.style.display = 'flex';
            renderInterestsView();
        }
    };

    // ==========================================
    // DOMAIN METADATA INFERENCE HELPER
    // ==========================================
    function inferDomainMeta(domainKey) {
        const dom = (domainKey || "general").toLowerCase();
        if (dom.includes('c-') || dom === 'c' || dom.includes('system') || dom.includes('pointer')) {
            return {
                title: "C & Systems Architecture",
                desc: "Low-level memory management, pointer invariants, bump arenas, and system bounds.",
                icon: "⚡"
            };
        }
        if (dom.includes('python') || dom === 'py') {
            return {
                title: "Python Programming Mastery",
                desc: "Tracking conceptual understanding, algorithmic structures, and execution agility from Python runtime runs.",
                icon: "🐍"
            };
        }
        if (dom.includes('js') || dom.includes('javascript') || dom.includes('web') || dom.includes('node')) {
            return {
                title: "JavaScript & Web Architecture",
                desc: "Event-driven paradigms, closures, asynchronous promises, and runtime execution.",
                icon: "🌐"
            };
        }
        if (dom.includes('java')) {
            return {
                title: "Java & Object-Oriented Design",
                desc: "Type safety, class hierarchies, and collections framework.",
                icon: "☕"
            };
        }
        if (dom.includes('algo') || dom.includes('structure') || dom.includes('dsa')) {
            return {
                title: "Algorithms & Complexity",
                desc: "Dynamic programming, binary search trees, divide-and-conquer, and state space reduction.",
                icon: "🧮"
            };
        }
        if (dom.includes('rust')) {
            return {
                title: "Rust & Systems Programming",
                desc: "Memory safety without garbage collection, borrow checker, and zero-cost abstractions.",
                icon: "🦀"
            };
        }
        if (dom.includes('go') || dom.includes('golang')) {
            return {
                title: "Go Programming & Concurrency",
                desc: "Goroutines, channels, interface composition, and standard library architectures.",
                icon: "🔵"
            };
        }

        const cleanName = domainKey.replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return {
            title: `${cleanName} Mastery`,
            desc: `Tracking concept mastery, syntax boundaries, and execution agility in ${cleanName}.`,
            icon: "💡"
        };
    }

    // ==========================================
    // 1. CODE MASTERY GRAPH SYNC & RENDER
    // ==========================================
    async function fetchAndSyncLiveGraph() {
        try {
            const kg = await window.API.getKnowledgeGraph();
            const nodes = (kg && Array.isArray(kg.nodes)) ? kg.nodes : [];

            // Compute data signature to completely eliminate any screen glitching/flicker
            const currentSignature = JSON.stringify(
                nodes.map(n => [n.skill_id, n.confidence, n.evidence_count, n.status, n.domain])
            );

            if (currentSignature === lastGraphSignature) {
                // Backend data unchanged, do not touch DOM
                return;
            }
            lastGraphSignature = currentSignature;

            // Rebuild dynamicCurriculum purely from real nodes
            dynamicCurriculum = {};

            nodes.forEach(node => {
                const domKey = (node.domain || "general").toLowerCase().replace(/[^a-z0-9_-]/g, '-');
                if (!dynamicCurriculum[domKey]) {
                    const meta = inferDomainMeta(domKey);
                    dynamicCurriculum[domKey] = {
                        key: domKey,
                        title: meta.title,
                        desc: meta.desc,
                        icon: meta.icon,
                        overallMastery: 0,
                        episodes: 0,
                        avgFriction: 0.0,
                        subtopics: []
                    };
                }

                const masteryPct = Math.min(100, Math.round((node.confidence || 0.5) * 100));
                const conceptName = node.name || node.label || (node.skill_id || node.id || "").replace(/^[a-z]+-/, '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || "Core Concept";
                const evCount = typeof node.evidence_count === 'number' ? node.evidence_count : 1;

                dynamicCurriculum[domKey].subtopics.push({
                    id: node.skill_id || node.id,
                    name: conceptName,
                    desc: `Evaluated across ${evCount} run episode${evCount > 1 ? 's' : ''}. Real-time mastery: ${masteryPct}%.`,
                    mastery: masteryPct,
                    episodes: evCount,
                    errors: node.status === 'developing' ? 1 : 0,
                    status: node.status === 'mastered' ? 'mastered' : node.confidence >= 0.5 ? 'proficient' : 'needs_work',
                    pitfalls: `Maintain clean invariant checks and boundary handling when working with ${conceptName}.`
                });
            });

            // Calculate overall mastery for each dynamic domain
            const domainKeys = Object.keys(dynamicCurriculum);
            domainKeys.forEach(k => {
                const topic = dynamicCurriculum[k];
                if (topic.subtopics.length > 0) {
                    const avg = Math.round(topic.subtopics.reduce((a, b) => a + b.mastery, 0) / topic.subtopics.length);
                    topic.overallMastery = avg;
                    topic.episodes = topic.subtopics.reduce((a, b) => a + b.episodes, 0);
                }
            });

            // If activeTopicKey is no longer in dynamicCurriculum, pick the first one or reset
            if (!activeTopicKey || !dynamicCurriculum[activeTopicKey]) {
                activeTopicKey = domainKeys.length > 0 ? domainKeys[0] : null;
            }

            if (currentMode === 'mastery') {
                renderMasteryView();
            }
        } catch (err) {
            console.debug("Live knowledge sync notice:", err);
        }
    }

    function renderMasteryView() {
        const domainKeys = Object.keys(dynamicCurriculum);

        // Render topic tabs
        topicTabsBar.innerHTML = '';
        if (domainKeys.length === 0) {
            topicTabsBar.style.display = 'none';
            topicBanner.style.display = 'none';
            sectionTitleRow.style.display = 'none';
            renderEmptyMasteryState();
            return;
        }

        topicTabsBar.style.display = 'flex';
        topicBanner.style.display = 'flex';
        sectionTitleRow.style.display = 'flex';

        domainKeys.forEach(key => {
            const topic = dynamicCurriculum[key];
            const tabBtn = document.createElement('button');
            tabBtn.className = `topic-tab ${key === activeTopicKey ? 'active' : ''}`;
            tabBtn.onclick = () => window.selectTopic(key);

            tabBtn.innerHTML = `
                <span class="tab-icon">${topic.icon}</span>
                <div class="tab-meta">
                    <span class="tab-name">${escapeHtml(topic.title.replace(' Mastery', ''))}</span>
                    <span class="tab-sub">${topic.subtopics.length} concept${topic.subtopics.length === 1 ? '' : 's'}</span>
                </div>
                <span class="tab-badge">${topic.overallMastery}%</span>
            `;
            topicTabsBar.appendChild(tabBtn);
        });

        // Render Active Topic
        if (activeTopicKey && dynamicCurriculum[activeTopicKey]) {
            renderTopic(activeTopicKey);
        }
    }

    function renderEmptyMasteryState() {
        subtopicsGrid.innerHTML = `
            <div class="empty-knowledge-state glass-card" style="grid-column: 1 / -1; text-align: center; padding: 60px 24px; border: 1px dashed rgba(255, 255, 255, 0.12); border-radius: 16px; margin: 12px 0;">
                <div style="font-size: 2.8rem; margin-bottom: 16px;">🌱</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #f8fafc; margin-bottom: 10px;">Knowledge Graph is Brand New & Empty</div>
                <div style="font-size: 0.95rem; color: var(--text-secondary); max-width: 560px; margin: 0 auto 20px auto; line-height: 1.6;">
                    Run your code files in the terminal or editor. Tesseract's Core Engine will automatically extract your programming languages, algorithmic topics, and concept boundaries, dynamically populating this graph with real-time mastery rings.
                </div>
                <div style="font-size: 0.85rem; color: #a5b4fc; font-family: monospace; background: rgba(99, 102, 241, 0.12); display: inline-block; padding: 8px 18px; border-radius: 8px; border: 1px solid rgba(99, 102, 241, 0.25);">
                    💡 Run any code (e.g. Python, C, JavaScript) to dynamically start mapping
                </div>
            </div>
        `;
    }

    window.selectTopic = function (topicKey) {
        if (!dynamicCurriculum[topicKey]) return;
        activeTopicKey = topicKey;

        // Update tab buttons
        document.querySelectorAll('.topic-tab').forEach((tab, index) => {
            const keys = Object.keys(dynamicCurriculum);
            if (keys[index] === topicKey) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        renderTopic(topicKey);
    };

    function renderTopic(topicKey) {
        const topic = dynamicCurriculum[topicKey];
        if (!topic) return;

        // Update Banner
        bannerTitle.textContent = topic.title;
        bannerDesc.textContent = topic.desc;
        bannerIcon.textContent = topic.icon;
        statSubtopics.textContent = topic.subtopics.length;
        statEpisodes.textContent = topic.episodes;
        statFriction.textContent = topic.episodes > 0 ? "Optimal (0.00)" : "Clean (0.00)";
        statFriction.style.color = '#10b981';

        // Animate Banner Radial Ring
        animateRadialRing(bannerRingFill, bannerRadialPct, topic.overallMastery);

        // Render Subtopics Grid
        renderSubtopicsList(topic.subtopics);
    }

    function renderSubtopicsList(subtopics) {
        subtopicsGrid.innerHTML = '';

        if (!subtopics || subtopics.length === 0) {
            subtopicCountSummary.textContent = "0 concepts recorded";
            return;
        }

        let filtered = subtopics.filter(st => {
            if (currentFilter === 'needs_work' && st.mastery >= 50) return false;
            if (currentFilter === 'mastered' && st.mastery < 75) return false;

            if (currentSearchTerm) {
                const term = currentSearchTerm.toLowerCase();
                const matched = st.name.toLowerCase().includes(term) || st.desc.toLowerCase().includes(term);
                if (!matched) return false;
            }
            return true;
        });

        subtopicCountSummary.textContent = `Showing ${filtered.length} of ${subtopics.length} concepts`;

        if (filtered.length === 0) {
            subtopicsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-tertiary);">
                    No concepts match the selected filter.
                </div>
            `;
            return;
        }

        filtered.forEach(st => {
            const card = document.createElement('div');
            card.className = 'subtopic-card';
            card.onclick = () => window.openConceptModal(st);

            const ringClass = getRingColorClass(st.mastery);
            const statusClass = st.mastery >= 75 ? 'mastered' : st.mastery >= 50 ? 'proficient' : 'needs_work';
            const statusLabel = st.mastery >= 75 ? 'Mastered' : st.mastery >= 50 ? 'Proficient' : 'Needs Work';

            const offset = CIRCUMFERENCE - (CIRCUMFERENCE * st.mastery) / 100;

            card.innerHTML = `
                <div class="card-top-row">
                    <div class="card-title-meta">
                        <div class="card-concept-title">${escapeHtml(st.name)}</div>
                        <div class="card-desc">${escapeHtml(st.desc)}</div>
                    </div>
                    <div class="radial-ring-container card-ring">
                        <svg viewBox="0 0 100 100" class="radial-svg">
                            <circle class="ring-bg" cx="50" cy="50" r="40"></circle>
                            <circle class="ring-fill ${ringClass}" cx="50" cy="50" r="40" 
                                stroke-dasharray="${CIRCUMFERENCE}" 
                                stroke-dashoffset="${offset}"></circle>
                        </svg>
                        <div class="radial-content">
                            <span class="radial-percentage">${st.mastery}%</span>
                        </div>
                    </div>
                </div>
                <div class="card-bottom-row">
                    <span class="status-badge ${statusClass}">${statusLabel}</span>
                    <span>Practiced ${st.episodes}x</span>
                </div>
            `;
            subtopicsGrid.appendChild(card);
        });
    }

    // ==========================================
    // 2. BROWSER INTERESTS & ROADMAP SYNC & RENDER
    // ==========================================
    async function fetchAndSyncInterests() {
        try {
            const data = await window.API.getBrowserInterests();
            cachedInterestsData = data;

            const currentSignature = JSON.stringify(data);
            if (currentSignature === lastInterestsSignature) {
                return;
            }
            lastInterestsSignature = currentSignature;

            if (currentMode === 'interests') {
                renderInterestsView();
            }
        } catch (err) {
            console.debug("Interests sync notice:", err);
        }
    }

    window.refreshInterests = async function (force = false) {
        if (force) {
            window.API.invalidateCache();
        }
        await fetchAndSyncInterests();
        if (window.Notifications) {
            window.Notifications.info('Interests Refreshed', 'Telemetry re-synchronized from browser sensors.');
        }
    };

    function renderInterestsView() {
        if (!cachedInterestsData || !Array.isArray(cachedInterestsData.interests)) {
            renderEmptyInterestsState();
            return;
        }

        const { interests, total_browser_events } = cachedInterestsData;
        const totalWatchMinutes = interests.reduce((acc, cur) => acc + (cur.stats?.watch_time_minutes || 0), 0);

        statInterestsCount.textContent = interests.length;
        statTotalWatchTime.textContent = `${Math.round(totalWatchMinutes)} min`;
        statBrowserEvents.textContent = total_browser_events || 0;

        if (interests.length === 0) {
            renderEmptyInterestsState();
            return;
        }

        let filtered = interests.filter(item => {
            if (currentInterestFilter !== 'all' && item.standing !== currentInterestFilter) {
                return false;
            }
            if (currentSearchTerm) {
                const term = currentSearchTerm.toLowerCase();
                const matched = item.title.toLowerCase().includes(term) ||
                    (item.recent_searches || []).some(s => s.toLowerCase().includes(term));
                if (!matched) return false;
            }
            return true;
        });

        interestsGrid.innerHTML = '';
        if (filtered.length === 0) {
            interestsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-tertiary);">
                    No browser interests match the selected filter.
                </div>
            `;
            return;
        }

        filtered.forEach(interest => {
            const card = document.createElement('div');
            card.className = 'interest-card glass-card';

            const offset = CIRCUMFERENCE - (CIRCUMFERENCE * interest.standing_score) / 100;
            const ringClass = getRingColorClass(interest.standing_score);

            // Roadmap Items
            let roadmapHtml = '';
            (interest.roadmap || []).forEach((rm, idx) => {
                const isDone = rm.completed;
                const statusBadge = isDone 
                    ? `<span class="roadmap-badge done">✓ Completed</span>` 
                    : `<span class="roadmap-badge rec">Recommended</span>`;
                
                roadmapHtml += `
                    <div class="roadmap-item ${isDone ? 'completed' : ''}">
                        <div class="roadmap-step-num">${idx + 1}</div>
                        <div class="roadmap-info">
                            <div class="roadmap-title-row">
                                <a href="${escapeHtml(rm.url)}" target="_blank" rel="noopener noreferrer" class="roadmap-title-link">
                                    ${escapeHtml(rm.title)}
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                                </a>
                                ${statusBadge}
                            </div>
                            <div class="roadmap-meta">
                                <span>📺 ${escapeHtml(rm.channel)}</span>
                                <span>⏱️ ${escapeHtml(rm.duration)}</span>
                                <span class="badge badge-sm">${escapeHtml(rm.level)}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            // Recent Searches Chips
            let searchesHtml = '';
            if (interest.recent_searches && interest.recent_searches.length > 0) {
                searchesHtml = `
                    <div class="interest-searches-box">
                        <span class="searches-label">Recent Searches:</span>
                        <div class="searches-chips">
                            ${interest.recent_searches.map(s => `<span class="search-chip">🔍 ${escapeHtml(s)}</span>`).join('')}
                        </div>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="interest-card-header">
                    <div class="interest-header-left">
                        <span class="interest-icon">${interest.icon || '🔍'}</span>
                        <div>
                            <h3 class="interest-title">${escapeHtml(interest.title)}</h3>
                            <div class="interest-standing-row">
                                <span class="standing-pill" style="border-color: ${interest.standing_color}; color: ${interest.standing_color}">
                                    ${interest.standing_badge}
                                </span>
                                <span class="text-muted" style="font-size: 0.8rem;">
                                    ${interest.stats.watch_time_minutes}m watched • ${interest.stats.searches_count} searches
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Standing Radial Ring -->
                    <div class="radial-ring-container card-ring">
                        <svg viewBox="0 0 100 100" class="radial-svg">
                            <circle class="ring-bg" cx="50" cy="50" r="40"></circle>
                            <circle class="ring-fill ${ringClass}" cx="50" cy="50" r="40" 
                                stroke-dasharray="${CIRCUMFERENCE}" 
                                stroke-dashoffset="${offset}"></circle>
                        </svg>
                        <div class="radial-content">
                            <span class="radial-percentage">${interest.standing_score}%</span>
                        </div>
                    </div>
                </div>

                <div class="interest-next-milestone">
                    <strong>🎯 Next Milestone:</strong> ${escapeHtml(interest.next_milestone)}
                </div>

                ${searchesHtml}

                <div class="interest-roadmap-section">
                    <div class="roadmap-heading">
                        <span>Curated Video Learning Roadmap</span>
                        <span class="roadmap-count">${(interest.roadmap || []).length} Milestones</span>
                    </div>
                    <div class="roadmap-list">
                        ${roadmapHtml}
                    </div>
                </div>
            `;

            interestsGrid.appendChild(card);
        });
    }

    function renderEmptyInterestsState() {
        interestsGrid.innerHTML = `
            <div class="empty-knowledge-state glass-card" style="grid-column: 1 / -1; text-align: center; padding: 60px 24px; border: 1px dashed rgba(255, 255, 255, 0.12); border-radius: 16px; margin: 12px 0;">
                <div style="font-size: 2.8rem; margin-bottom: 16px;">🌐</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #f8fafc; margin-bottom: 10px;">No Browser Interests Discovered Yet</div>
                <div style="font-size: 0.95rem; color: var(--text-secondary); max-width: 560px; margin: 0 auto 20px auto; line-height: 1.6;">
                    Browse developer documentation, perform technical searches on Google/Bing/DuckDuckGo, or watch programming tutorials on YouTube with the Tesseract Browser Sensor active.
                </div>
                <div style="font-size: 0.85rem; color: #38bdf8; font-family: monospace; background: rgba(56, 189, 248, 0.12); display: inline-block; padding: 8px 18px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.25);">
                    🚀 Tip: Load the extension in Firefox/Brave and research any tech topic to auto-generate roadmaps
                </div>
            </div>
        `;
    }

    // ==========================================
    // CONTROLS & MODALS
    // ==========================================
    function animateRadialRing(circleEl, textEl, targetPercentage) {
        if (!circleEl || !textEl) return;
        const offset = CIRCUMFERENCE - (CIRCUMFERENCE * targetPercentage) / 100;
        circleEl.style.strokeDashoffset = offset;
        textEl.textContent = `${targetPercentage}%`;
        circleEl.className.baseVal = `ring-fill ${getRingColorClass(targetPercentage)}`;
    }

    function getRingColorClass(percentage) {
        if (percentage >= 75) return 'ring-emerald';
        if (percentage >= 50) return 'ring-indigo';
        if (percentage >= 25) return 'ring-amber';
        return 'ring-rose';
    }

    window.handleSearchInput = function (val) {
        currentSearchTerm = val.trim();
        if (currentMode === 'mastery') {
            if (activeTopicKey && dynamicCurriculum[activeTopicKey]) {
                renderSubtopicsList(dynamicCurriculum[activeTopicKey].subtopics);
            }
        } else {
            renderInterestsView();
        }
    };

    window.setFilter = function (filter, btn) {
        currentFilter = filter;
        document.querySelectorAll('#mastery-filters .filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (activeTopicKey && dynamicCurriculum[activeTopicKey]) {
            renderSubtopicsList(dynamicCurriculum[activeTopicKey].subtopics);
        }
    };

    window.setInterestFilter = function (filter, btn) {
        currentInterestFilter = filter;
        document.querySelectorAll('#interests-filters .filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderInterestsView();
    };

    // Modal Drawer
    const modalBackdrop = document.getElementById('concept-modal-backdrop');
    const modalTitle = document.getElementById('modal-concept-title');
    const modalDomain = document.getElementById('modal-domain-tag');
    const modalDesc = document.getElementById('modal-concept-desc');
    const modalPitfalls = document.getElementById('modal-pitfalls');
    const modalBadge = document.getElementById('modal-status-badge');
    const modalRingFill = document.getElementById('modal-ring-fill');
    const modalRingPct = document.getElementById('modal-ring-pct');
    const modalStatEpisodes = document.getElementById('modal-stat-episodes');
    const modalStatErrors = document.getElementById('modal-stat-errors');
    const modalStatConfidence = document.getElementById('modal-stat-confidence');
    const btnAskTutor = document.getElementById('btn-ask-tutor-concept');

    window.openConceptModal = function (concept) {
        selectedConceptData = concept;
        const topic = activeTopicKey && dynamicCurriculum[activeTopicKey] ? dynamicCurriculum[activeTopicKey] : null;
        const conceptName = concept.name || "Core Concept";

        modalTitle.textContent = conceptName;
        modalDomain.textContent = `${topic ? topic.title : 'General'} / Live`;
        modalDesc.textContent = concept.desc || `Evaluated across ${concept.episodes || 1} runtime episodes.`;
        modalPitfalls.textContent = concept.pitfalls || `Maintain clean invariant checks and boundary handling when working with ${conceptName}.`;

        const epCount = concept.episodes || 1;
        modalStatEpisodes.textContent = `${epCount} episode${epCount > 1 ? 's' : ''}`;
        modalStatErrors.textContent = `${concept.errors || 0}`;
        modalStatConfidence.textContent = concept.mastery >= 75 ? "High (0.90)" : concept.mastery >= 50 ? "Medium (0.60)" : "Developing (0.35)";

        modalBadge.textContent = concept.mastery >= 75 ? 'Mastered' : concept.mastery >= 50 ? 'Proficient' : 'Needs Practice';
        modalBadge.className = `badge status-badge ${concept.mastery >= 75 ? 'mastered' : concept.mastery >= 50 ? 'proficient' : 'needs_work'}`;

        animateRadialRing(modalRingFill, modalRingPct, concept.mastery);

        btnAskTutor.textContent = `💬 Ask Tutor About "${conceptName}"`;
        modalBackdrop.style.display = 'flex';
    };

    window.closeConceptModal = function (e) {
        if (e && e.target !== modalBackdrop && !e.target.classList.contains('modal-close-btn') && e.target.tagName !== 'BUTTON') {
            return;
        }
        modalBackdrop.style.display = 'none';
        selectedConceptData = null;
    };

    window.askTutorAboutConcept = function () {
        if (!selectedConceptData) return;
        const conceptName = selectedConceptData.name || "this concept";
        const topic = activeTopicKey && dynamicCurriculum[activeTopicKey] ? dynamicCurriculum[activeTopicKey].title : "programming";
        const prompt = `Can you explain the core concepts, best practices, and common gotchas for "${conceptName}" in ${topic}?`;
        sessionStorage.setItem('tesseract_initial_prompt', prompt);
        window.location.href = '/chat';
    };

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

})();
