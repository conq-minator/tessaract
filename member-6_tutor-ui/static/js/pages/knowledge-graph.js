/**
 * Tesseract Topic & Subtopic Knowledge Mastery Dashboard
 * Features Cursor-inspired circular progress rings with SVG dashoffset visualization.
 */

(function () {
    const CIRCUMFERENCE = 251.2; // 2 * Math.PI * 40

    // Master curriculum data organized by Topic -> Subtopics
    const CURRICULUM_DATA = {
        python: {
            title: "Python Programming Mastery",
            desc: "Tracking conceptual understanding, syntax boundaries, and debugging agility across Python runtime episodes.",
            icon: "🐍",
            overallMastery: 82,
            episodes: 18,
            avgFriction: 0.18,
            subtopics: [
                {
                    id: "py_loops",
                    name: "Loops & Iterations",
                    desc: "Loop bounds, range generation, and off-by-one indexing prevention in sequences.",
                    mastery: 88,
                    episodes: 6,
                    errors: 0,
                    status: "mastered",
                    pitfalls: "Using range(1, len(items) + 1) instead of range(len(items)) causes IndexError on the last iteration."
                },
                {
                    id: "py_defaults",
                    name: "Mutable Default Arguments",
                    desc: "Function signatures, evaluation timing, and avoiding shared state leakage across distinct calls.",
                    mastery: 75,
                    episodes: 4,
                    errors: 1,
                    status: "mastered",
                    pitfalls: "def func(items=[]) evaluates the list once at definition time, sharing the same list instance across all callers."
                },
                {
                    id: "py_math",
                    name: "Zero Division & Math Safety",
                    desc: "Guard conditions, empty filter handles, and denominator verification in averages.",
                    mastery: 85,
                    episodes: 3,
                    errors: 1,
                    status: "mastered",
                    pitfalls: "Filtered lists can be empty when no elements meet thresholds, leading to division by zero on sum/len."
                },
                {
                    id: "py_none",
                    name: "NoneType & Attribute Safety",
                    desc: "Safe attribute dereferencing, optional handling, and dictionary get() lookups.",
                    mastery: 70,
                    episodes: 2,
                    errors: 1,
                    status: "proficient",
                    pitfalls: "Accessing record.get() when record itself is None raises AttributeError: 'NoneType' object has no attribute 'get'."
                },
                {
                    id: "py_dict",
                    name: "Dictionary Key Lookups",
                    desc: "Key existence checking, defaultdict usage, and KeyError prevention patterns.",
                    mastery: 92,
                    episodes: 5,
                    errors: 0,
                    status: "mastered",
                    pitfalls: "Direct bracket indexing dict[key] crashes if key does not exist. Use dict.get(key, default)."
                },
                {
                    id: "py_recursion",
                    name: "Recursion & Call Stack",
                    desc: "Base case termination, recursion limits, and accumulator transformations.",
                    mastery: 45,
                    episodes: 2,
                    errors: 2,
                    status: "needs_work",
                    pitfalls: "Failing to decrement parameters towards a base case triggers infinite recursion and RecursionError."
                }
            ]
        },
        c: {
            title: "C & Systems Architecture",
            desc: "Pointers, memory management, buffer boundaries, and defensive systems programming.",
            icon: "⚡",
            overallMastery: 68,
            episodes: 12,
            avgFriction: 0.28,
            subtopics: [
                {
                    id: "c_pointers",
                    name: "Pointers & Dereferencing",
                    desc: "Address-of operators, pointer arithmetic, and valid memory references.",
                    mastery: 65,
                    episodes: 4,
                    errors: 2,
                    status: "proficient",
                    pitfalls: "Dereferencing uninitialized pointers or dangling pointers causes immediate segmentation faults."
                },
                {
                    id: "c_null",
                    name: "Null Pointer Safety",
                    desc: "Defensive NULL assertions, guard clauses, and error exit strategies.",
                    mastery: 85,
                    episodes: 3,
                    errors: 0,
                    status: "mastered",
                    pitfalls: "Always check if (ptr == NULL) before writing or reading through any pointer passed to a function."
                },
                {
                    id: "c_alloc",
                    name: "Dynamic Memory (malloc/free)",
                    desc: "Heap allocation life-cycles, avoiding memory leaks, and double free prevention.",
                    mastery: 55,
                    episodes: 3,
                    errors: 1,
                    status: "proficient",
                    pitfalls: "Every malloc must have exactly one corresponding free. Set freed pointers to NULL immediately."
                },
                {
                    id: "c_buffers",
                    name: "Array Bounds & Buffers",
                    desc: "Fixed-size buffer safety, strcpy vs strncpy, and stack smashing defense.",
                    mastery: 40,
                    episodes: 2,
                    errors: 2,
                    status: "needs_work",
                    pitfalls: "Unbounded string operations allow buffer overflow attacks and corrupt return addresses on the stack."
                }
            ]
        },
        javascript: {
            title: "JavaScript & Web Architecture",
            desc: "Asynchronous concurrency, scope closures, DOM event binding, and JSON protocols.",
            icon: "🌐",
            overallMastery: 74,
            episodes: 15,
            avgFriction: 0.22,
            subtopics: [
                {
                    id: "js_scope",
                    name: "Variable Scope & TDZ",
                    desc: "let, const, and var hoisting behavior and Temporal Dead Zone avoidance.",
                    mastery: 80,
                    episodes: 4,
                    errors: 1,
                    status: "mastered",
                    pitfalls: "Referencing a let or const variable before its initialization line throws ReferenceError: Cannot access before initialization."
                },
                {
                    id: "js_async",
                    name: "Async / Await & Promises",
                    desc: "Event loop microtask queues, unhandled promise rejections, and try/catch async blocks.",
                    mastery: 65,
                    episodes: 5,
                    errors: 2,
                    status: "proficient",
                    pitfalls: "Forgetting to await a promise causes subsequent lines to operate on a pending Promise object instead of the resolved value."
                },
                {
                    id: "js_json",
                    name: "JSON Parsing & Serialization",
                    desc: "Strict JSON format standards, trailing comma traps, and safe JSON.parse wrapping.",
                    mastery: 85,
                    episodes: 3,
                    errors: 0,
                    status: "mastered",
                    pitfalls: "JSON.parse crashes synchronously on trailing commas or single-quoted strings. Always wrap with try/catch."
                },
                {
                    id: "js_dom",
                    name: "DOM Event Binding",
                    desc: "Script execution order, defer/async attributes, and null element event listeners.",
                    mastery: 70,
                    episodes: 3,
                    errors: 1,
                    status: "proficient",
                    pitfalls: "Calling addEventListener on document.getElementById before DOMContentLoaded runs causes TypeError: Cannot read properties of null."
                }
            ]
        },
        java: {
            title: "Java & Object-Oriented Design",
            desc: "Type safety, class hierarchies, exception contracts, and collections framework.",
            icon: "☕",
            overallMastery: 60,
            episodes: 8,
            avgFriction: 0.32,
            subtopics: [
                {
                    id: "java_null",
                    name: "NullPointer Defense",
                    desc: "Optional<T> usage, Objects.requireNonNull, and defensive parameter validation.",
                    mastery: 72,
                    episodes: 3,
                    errors: 1,
                    status: "proficient",
                    pitfalls: "Calling methods on references returned from search or map without checking for null throws NullPointerException."
                },
                {
                    id: "java_oop",
                    name: "Inheritance & Polymorphism",
                    desc: "Abstract classes, interface default methods, and dynamic dispatch principles.",
                    mastery: 68,
                    episodes: 3,
                    errors: 1,
                    status: "proficient",
                    pitfalls: "Violating the Liskov Substitution Principle causes subtle runtime bugs when swapping subclass implementations."
                },
                {
                    id: "java_collec",
                    name: "Collections Framework",
                    desc: "List, Set, and Map selection, iterator concurrency, and equals/hashCode contracts.",
                    mastery: 50,
                    episodes: 2,
                    errors: 2,
                    status: "in_progress",
                    pitfalls: "Modifying a collection while iterating over it without using Iterator.remove() throws ConcurrentModificationException."
                }
            ]
        },
        algorithms: {
            title: "Algorithms & Complexity",
            desc: "Big-O space/time complexity, search space reduction, and inductive data structures.",
            icon: "🧮",
            overallMastery: 55,
            episodes: 9,
            avgFriction: 0.35,
            subtopics: [
                {
                    id: "algo_bsearch",
                    name: "Binary Search & Invariants",
                    desc: "Sorted array search, midpoint calculation without overflow, and range termination.",
                    mastery: 70,
                    episodes: 3,
                    errors: 1,
                    status: "proficient",
                    pitfalls: "Midpoint formula (low + high) / 2 can overflow in fixed integer types. Prefer low + (high - low) / 2."
                },
                {
                    id: "algo_sort",
                    name: "Sorting Algorithms",
                    desc: "Divide-and-conquer, partition invariants in QuickSort, and stability in MergeSort.",
                    mastery: 52,
                    episodes: 3,
                    errors: 2,
                    status: "in_progress",
                    pitfalls: "Worst-case quadratic time in naive QuickSort on already-sorted arrays without randomized pivot selection."
                },
                {
                    id: "algo_trees",
                    name: "Tree Traversals & Recursion",
                    desc: "Depth-first (in-order, pre-order, post-order) and breadth-first queue traversals.",
                    mastery: 45,
                    episodes: 3,
                    errors: 2,
                    status: "needs_work",
                    pitfalls: "Failing to check null on left and right child pointers causes recursive traversal to crash."
                }
            ]
        }
    };

    let activeTopicKey = 'python';
    let currentFilter = 'all';
    let currentSearchTerm = '';
    let selectedConceptData = null;

    // Elements
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
        // Render initial topic
        renderTopic(activeTopicKey);

        // Try pulling live knowledge data from backend if available
        try {
            const kg = await window.API.getKnowledgeGraph();
            if (kg && kg.nodes) {
                // Incorporate live node statuses
                console.debug("Live knowledge nodes available:", kg.nodes.length);
            }
        } catch (e) {
            console.debug("Using cached curriculum data:", e);
        }
    });

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
        statFriction.textContent = topic.avgFriction < 0.25 ? `Low (${topic.avgFriction})` : `Med (${topic.avgFriction})`;
        statFriction.style.color = topic.avgFriction < 0.25 ? '#10b981' : '#f59e0b';

        // Animate Banner Radial Ring
        animateRadialRing(bannerRingFill, bannerRadialPct, topic.overallMastery);

        // Render Subtopics Grid
        renderSubtopicsList(topic.subtopics);
    }

    function renderSubtopicsList(subtopics) {
        subtopicsGrid.innerHTML = '';

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
            card.className = 'subtopic-card animate-fade-in';
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
        modalTitle.textContent = concept.name;
        modalDomain.textContent = `${CURRICULUM_DATA[activeTopicKey].title} / Core`;
        modalDesc.textContent = concept.desc;
        modalPitfalls.textContent = concept.pitfalls || "Keep variable types and boundary checks explicit in your active code.";

        modalStatEpisodes.textContent = `${concept.episodes} episodes`;
        modalStatErrors.textContent = `${concept.errors}`;
        modalStatConfidence.textContent = concept.mastery >= 75 ? "High (0.85)" : concept.mastery >= 50 ? "Medium (0.60)" : "Low (0.35)";

        // Status badge
        modalBadge.textContent = concept.mastery >= 75 ? 'Mastered' : concept.mastery >= 50 ? 'Proficient' : 'Needs Practice';
        modalBadge.className = `badge status-badge ${concept.mastery >= 75 ? 'mastered' : concept.mastery >= 50 ? 'proficient' : 'needs_work'}`;

        // Animate Modal Ring
        animateRadialRing(modalRingFill, modalRingPct, concept.mastery);

        btnAskTutor.textContent = `💬 Ask Tutor About "${concept.name}"`;
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
        const prompt = `Can you explain the core concepts, best practices, and common gotchas for "${selectedConceptData.name}" in ${CURRICULUM_DATA[activeTopicKey].title}?`;
        // Navigate to /chat with pre-filled prompt
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
