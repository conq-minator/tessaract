/**
 * Learning Page Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch recommendations directly from API
        const recs = await window.API.getRecommendations();
        renderRecommendations(recs);
        
        // Render fake roadmap data since Member 4 API mock doesn't fully cover roadmap yet
        // In a real scenario we'd fetch roadmap here
        const fakeRoadmap = {
            subject: "C Programming",
            current_level: "Intermediate",
            estimated_completion: "14 hours",
            milestones: [
                {
                    topic: "Memory Layout & Variables",
                    status: "completed",
                    estimated_hours: 2,
                    subtopics: [
                        { topic: "Stack vs Heap", status: "completed" },
                        { topic: "Variable Scope", status: "completed" }
                    ]
                },
                {
                    topic: "Pointers Fundamentals",
                    status: "active",
                    estimated_hours: 4,
                    subtopics: [
                        { topic: "Pointer Syntax", status: "completed" },
                        { topic: "Dereferencing", status: "active" },
                        { topic: "Pointer Arithmetic", status: "pending" }
                    ]
                },
                {
                    topic: "Advanced Data Structures",
                    status: "pending",
                    estimated_hours: 8,
                    subtopics: [
                        { topic: "Linked Lists", status: "pending" },
                        { topic: "Binary Trees", status: "pending" }
                    ]
                }
            ]
        };
        renderRoadmap(fakeRoadmap);

    } catch (e) {
        console.error("Failed to load learning data:", e);
    }
});

function renderRecommendations(recs) {
    const list = document.getElementById('rec-list');
    list.innerHTML = '';
    
    if (!recs || recs.length === 0) {
        list.innerHTML = '<div class="text-muted">No recommendations right now.</div>';
        return;
    }
    
    recs.forEach(rec => {
        const html = `
            <a href="${rec.url}" target="_blank" class="rec-item">
                <div class="rec-title">${rec.title}</div>
                <div class="rec-meta">
                    <span class="badge badge-primary">${rec.format}</span>
                    <span>Diff: ${rec.difficulty}</span>
                </div>
            </a>
        `;
        list.insertAdjacentHTML('beforeend', html);
    });
}

function renderRoadmap(data) {
    document.getElementById('rm-subject').textContent = data.subject;
    document.getElementById('rm-level').textContent = data.current_level;
    document.getElementById('rm-eta').textContent = data.estimated_completion;
    
    const timeline = document.getElementById('rm-timeline');
    timeline.innerHTML = '';
    
    data.milestones.forEach(ms => {
        let subtopicsHtml = ms.subtopics.map(sub => {
            const cls = sub.status === 'completed' ? 'completed' : '';
            return `<span class="subtopic ${cls}">${sub.topic}</span>`;
        }).join('');
        
        const html = `
            <div class="milestone ${ms.status}">
                <div class="ms-title">${ms.topic}</div>
                <div class="ms-meta">Est: ${ms.estimated_hours}h &bull; Status: ${ms.status.toUpperCase()}</div>
                <div class="subtopics">
                    ${subtopicsHtml}
                </div>
            </div>
        `;
        timeline.insertAdjacentHTML('beforeend', html);
    });
}
