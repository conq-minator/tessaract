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
                renderHistoryTable(allEpisodes.filter(ep => ep.status === filter));
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
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No episodes found</td></tr>';
        return;
    }
    
    episodes.forEach(ep => {
        let badgeClass = 'badge-primary';
        if (ep.status === 'mastered') badgeClass = 'badge-success';
        else if (ep.status === 'struggling') badgeClass = 'badge-warning';
        
        const html = `
            <tr>
                <td class="topic-cell">${ep.topic}</td>
                <td>${ep.duration_min} min</td>
                <td>${ep.friction.toFixed(2)}</td>
                <td><span class="badge ${badgeClass}">${ep.status}</span></td>
            </tr>
        `;
        tbody.insertAdjacentHTML('beforeend', html);
    });
}
