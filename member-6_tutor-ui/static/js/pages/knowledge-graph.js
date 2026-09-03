/**
 * Tesseract Topic & Subtopic Knowledge Mastery Dashboard
 * Dynamically populated directly from real code executions with Cursor-inspired circular progress rings.
 */

(function () {
    const CIRCUMFERENCE = 251.2; // 2 * Math.PI * 40

    // Master curriculum metadata - Subtopics start 100% EMPTY and are added ONLY upon real code execution!
    const CURRICULUM_DATA = {
        python: {
            title: "Python Programming Mastery",
            desc: "Tracking conceptual understanding, algorithmic structures, and execution agility from your Python code runs.",
            icon: "🐍",
            overallMastery: 0,
            episodes: 0,
            avgFriction: 0.0,
            subtopics: []
        },
        c: {
            title: "C & Systems Architecture",
            desc: "Low-level memory management, pointer invariants, bump arenas, and system bounds.",
            icon: "⚡",
            overallMastery: 0,
            episodes: 0,
            avgFriction: 0.0,
            subtopics: []
        },
        javascript: {
            title: "JavaScript & Web Architecture",
            desc: "Event-driven paradigms, closures, asynchronous promises, and callback registries.",
            icon: "🌐",
            overallMastery: 0,
            episodes: 0,
            avgFriction: 0.0,
            subtopics: []
        },
        java: {
            title: "Java & Object-Oriented Design",
            desc: "Type safety, class hierarchies, and collections framework.",
            icon: "☕",
            overallMastery: 0,
            episodes: 0,
            avgFriction: 0.0,
            subtopics: []
        },
        algorithms: {
            title: "Algorithms & Complexity",
            desc: "Dynamic programming, binary search trees, divide-and-conquer, and state space reduction.",
            icon: "🧮",
            overallMastery: 0,
            episodes: 0,
            avgFriction: 0.0,
            subtopics: []
        }
    };

    let activeTopicKey = 'python';
    let currentFilter = 'all';
    let currentSearchTerm = '';
    let selectedConceptData = null;
    let lastGraphSignature = '';

    // DOM Elements
    const subtopicsGrid = document.getElementById('subtopics-grid');
    const bannerTitle = document.getElementById('banner-title');
    const bannerDesc = document.getElementById('banner-desc');
    const bannerIcon = document.getElementById('banner-icon');
    const bannerRadialPct = document.getElementById('banner-radial-pct');
    const bannerRingFill = document.getElementById('banner-ring-fill');
    const statSubtopics = document.getElementById('stat-subtopics-count');
    const statEpisodes = document.getElementById('stat-episodes-count');
    const statFriction = document.getElementById('stat-friction-rate');
    const subtopicCountSummary = document.getElementById('subtopic-count-summary');

    document.addEventListener('DOMContentLoaded', async () => {
        // Initial render of empty state
        renderTopic(activeTopicKey);

        // Immediate fetch from backend
        await fetchAndSyncLiveGraph();

        // Polling sync every 3s — BUT only re-renders DOM if the graph data signature ACTUALLY changes!
        setInterval(fetchAndSyncLiveGraph, 3000);
    });

    async function fetchAndSyncLiveGraph() {
        try {
            const kg = await window.API.getKnowledgeGraph();
            const nodes = (kg && Array.isArray(kg.nodes)) ? kg.nodes : [];

            // Compute data signature to completely eliminate any screen glitching/flicker
            const currentSignature = JSON.stringify(
                nodes.map(n => [n.skill_id, n.confidence, n.evidence_count, n.status])
            );

            if (currentSignature === lastGraphSignature) {
                // Absolutely nothing changed in backend data, DO NOT touch or glitch the DOM!
                return;
            }
            lastGraphSignature = currentSignature;

            // Reset subtopics for all topics to rebuild purely from real evidence
            for (const key of Object.keys(CURRICULUM_DATA)) {
                CURRICULUM_DATA[key].subtopics = [];
                CURRICULUM_DATA[key].overallMastery = 0;
                CURRICULUM_DATA[key].episodes = 0;
            }

            // Map live nodes directly into their corresponding domains
            nodes.forEach(node => {
                const dom = (node.domain || "python").toLowerCase();
                let key = 'python';
                if (dom.includes('c-') || dom === 'c' || dom.includes('system') || dom.includes('pointer')) key = 'c';
                else if (dom.includes('js') || dom.includes('javascript') || dom.includes('web')) key = 'javascript';
                else if (dom.includes('java')) key = 'java';
                else if (dom.includes('algo') || dom.includes('structure')) key = 'algorithms';
                else key = 'python';

                if (!CURRICULUM_DATA[key]) return;

                const masteryPct = Math.min(100, Math.round((node.confidence || 0.5) * 100));
                const conceptName = node.name || node.label || (node.skill_id || node.id || "").replace(/^[a-z]+-/, '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || "Core Concept";
                const evCount = typeof node.evidence_count === 'number' ? node.evidence_count : 1;

                CURRICULUM_DATA[key].subtopics.push({
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

            // Recalculate domain mastery and update tab badges
            for (const [key, topic] of Object.entries(CURRICULUM_DATA)) {
                const badgeEl = document.getElementById(`badge-${key}`);
                if (topic.subtopics.length > 0) {
                    const avg = Math.round(topic.subtopics.reduce((a, b) => a + b.mastery, 0) / topic.subtopics.length);
                    topic.overallMastery = avg;
                    topic.episodes = topic.subtopics.reduce((a, b) => a + b.episodes, 0);
                    if (badgeEl) badgeEl.textContent = `${avg}%`;
                } else {
                    topic.overallMastery = 0;
                    topic.episodes = 0;
                    if (badgeEl) badgeEl.textContent = `0%`;
                }
            }

            // Smoothly render without screen tearing
            renderTopic(activeTopicKey);
        } catch (err) {
            console.debug("Live knowledge sync notice:", err);
        }
    }

    window.selectTopic = function (topicKey) {
        if (!CURRICULUM_DATA[topicKey]) return;
        activeTopicKey = topicKey;

        // Update tab buttons
        document.querySelectorAll('.topic-tab').forEach(tab => {
            if (tab.dataset.topic === topicKey) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        renderTopic(topicKey);
    };

    function renderTopic(topicKey) {
        const topic = CURRICULUM_DATA[topicKey];
        if (!topic) return;

        // Update Banner
        bannerTitle.textContent = topic.title;
        bannerDesc.textContent = topic.desc;
        bannerIcon.textContent = topic.icon;
        statSubtopics.textContent = topic.subtopics.length;
        statEpisodes.textContent = topic.episodes;
        statFriction.textContent = topic.episodes > 0 ? (topic.avgFriction < 0.25 ? "Optimal (0.00)" : "Moderate") : "Clean (0.00)";
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
            subtopicsGrid.innerHTML = `
                <div class="empty-knowledge-state" style="grid-column: 1 / -1; text-align: center; padding: 48px 24px; background: rgba(255, 255, 255, 0.02); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 14px; margin: 12px 0;">
                    <div style="font-size: 2.2rem; margin-bottom: 12px;">🌱</div>
                    <div style="font-size: 1.15rem; font-weight: 600; color: #f8fafc; margin-bottom: 8px;">No Concepts Discovered Yet</div>
                    <div style="font-size: 0.875rem; color: var(--text-tertiary); max-width: 500px; margin: 0 auto 16px auto; line-height: 1.5;">
                        Run your code files in the terminal or editor. Tesseract will automatically extract the programming topics, algorithms, and data structures, and map them here with real-time mastery rings.
                    </div>
                    <div style="font-size: 0.8rem; color: #818cf8; font-family: monospace; background: rgba(99, 102, 241, 0.1); display: inline-block; padding: 6px 14px; border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.2);">
                        Run any code in terminal to start mapping
                    </div>
                </div>
            `;
            return;
        }

        let filtered = subtopics.filter(st => {
            // Status filter
            if (currentFilter === 'needs_work' && st.mastery >= 50) return false;
            if (currentFilter === 'mastered' && st.mastery < 75) return false;

            // Search filter
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
            // Clean card without glitchy re-animation
            card.className = 'subtopic-card';
            card.onclick = () => window.openConceptModal(st);

            const ringClass = getRingColorClass(st.mastery);
            const statusClass = st.mastery >= 75 ? 'mastered' : st.mastery >= 50 ? 'proficient' : 'needs_work';
            const statusLabel = st.mastery >= 75 ? 'Mastered' : st.mastery >= 50 ? 'Proficient' : 'Needs Work';

            // Calculate SVG dashoffset
            const offset = CIRCUMFERENCE - (CIRCUMFERENCE * st.mastery) / 100;

            card.innerHTML = `
                <div class="card-top-row">
                    <div class="card-title-meta">
                        <div class="card-concept-title">${escapeHtml(st.name)}</div>
                        <div class="card-desc">${escapeHtml(st.desc)}</div>
                    </div>
                    <!-- Cursor Token Ring Aesthetic -->
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

    function animateRadialRing(circleEl, textEl, targetPercentage) {
        const offset = CIRCUMFERENCE - (CIRCUMFERENCE * targetPercentage) / 100;
        circleEl.style.strokeDashoffset = offset;
        textEl.textContent = `${targetPercentage}%`;

        // Color class
        circleEl.className.baseVal = `ring-fill ${getRingColorClass(targetPercentage)}`;
    }

    function getRingColorClass(percentage) {
        if (percentage >= 75) return 'ring-emerald';
        if (percentage >= 50) return 'ring-indigo';
        if (percentage >= 25) return 'ring-amber';
        return 'ring-rose';
    }

    // Search and Filter Controls
    window.filterSubtopics = function (val) {
        currentSearchTerm = val.trim();
        const topic = CURRICULUM_DATA[activeTopicKey];
        if (topic) renderSubtopicsList(topic.subtopics);
    };

    window.setFilter = function (filter, btn) {
        currentFilter = filter;
        document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const topic = CURRICULUM_DATA[activeTopicKey];
        if (topic) renderSubtopicsList(topic.subtopics);
    };

    // Concept Detail Modal
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
        const conceptName = concept.name || "Core Concept";
        modalTitle.textContent = conceptName;
        modalDomain.textContent = `${CURRICULUM_DATA[activeTopicKey].title} / Live`;
        modalDesc.textContent = concept.desc || `Evaluated across ${concept.episodes || 1} runtime episodes.`;
        modalPitfalls.textContent = concept.pitfalls || `Maintain clean invariant checks and boundary handling when working with ${conceptName}.`;

        const epCount = concept.episodes || 1;
        modalStatEpisodes.textContent = `${epCount} episode${epCount > 1 ? 's' : ''}`;
        modalStatErrors.textContent = `${concept.errors || 0}`;
        modalStatConfidence.textContent = concept.mastery >= 75 ? "High (0.90)" : concept.mastery >= 50 ? "Medium (0.60)" : "Developing (0.35)";

        // Status badge
        modalBadge.textContent = concept.mastery >= 75 ? 'Mastered' : concept.mastery >= 50 ? 'Proficient' : 'Needs Practice';
        modalBadge.className = `badge status-badge ${concept.mastery >= 75 ? 'mastered' : concept.mastery >= 50 ? 'proficient' : 'needs_work'}`;

        // Animate Modal Ring
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
        const prompt = `Can you explain the core concepts, best practices, and common gotchas for "${conceptName}" in ${CURRICULUM_DATA[activeTopicKey].title}?`;
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
