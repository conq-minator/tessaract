/**
 * History Page Logic
 */

let allEpisodes = [];

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const episodes = await window.API.getEpisodes();
        allEpisodes = episodes || [];
        renderHistoryTable(allEpisodes);
        
        document.getElementById('history-filter').addEventListener('change', (e) => {
            const filter = e.target.value;
            if (filter === 'all') {
                renderHistoryTable(allEpisodes);
            } else {
                renderHistoryTable(allEpisodes.filter(ep => {
                    const status = ep.outcome || ep.status || 'ongoing';
                    return status === filter;
                }));
            }
        });
    } catch (e) {
        console.error("Failed to load history data:", e);
        document.getElementById('history-table-body').innerHTML = `
            <tr><td colspan="4" class="text-center text-muted">Failed to load history</td></tr>
        `;
    }
});

function renderHistoryTable(episodes) {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';
    
    if (episodes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No episodes recorded yet</td></tr>';
        return;
    }
    
    episodes.forEach(ep => {
        const fScore = typeof ep.friction_score === 'number' 
            ? ep.friction_score 
            : (typeof ep.friction === 'number' ? ep.friction : 0);
        const status = ep.outcome || ep.status || 'ongoing';
        const topic = ep.topic || 'General Activity';
        const eventsCount = ep.events_count || ep.events || 1;
        
        let badgeClass = 'badge-primary';
        if (status === 'mastered' || status === 'resolved') badgeClass = 'badge-success';
        else if (status === 'struggling' || fScore > 0.5) badgeClass = 'badge-warning';
        
        const html = `
            <tr>
                <td class="topic-cell">${topic}</td>
                <td>${eventsCount} events</td>
                <td>${fScore.toFixed(2)}</td>
                <td><span class="badge ${badgeClass}">${status}</span></td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', html);
    });
}
