/**
 * Overview Page Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch data concurrently
        const [context, session, friction, episodes] = await Promise.all([
            window.API.getContext(),
            window.API.getSession(),
            window.API.getFriction(),
            window.API.getEpisodes()
        ]);

        // Render Context
        if (context) {
            document.getElementById('ui-subject').textContent = context.subject || 'Unknown';
            document.getElementById('ui-topic').textContent = context.topic || 'No topic';
            document.getElementById('ui-app').textContent = context.application || 'System';
        }

        // Render Session
        if (session) {
            document.getElementById('ui-session-time').textContent = session.duration || '0m';
            document.getElementById('ui-session-events').textContent = session.event_count || '0';
        }

        // Render Friction
        if (friction) {
            const score = friction.score || 0;
            const fill = document.getElementById('ui-friction-fill');
            const badge = document.getElementById('ui-friction-badge');
            
            document.getElementById('ui-friction-score').textContent = score.toFixed(2);
            fill.style.width = `${Math.min(100, score * 100)}%`;
            
            badge.textContent = friction.level || 'LOW';
            badge.className = 'badge'; // reset
            if (score > 0.7) badge.classList.add('badge-danger');
            else if (score > 0.4) badge.classList.add('badge-warning');
            else badge.classList.add('badge-success');
        }

        // Render Episodes
        if (episodes && Array.isArray(episodes)) {
            const list = document.getElementById('ui-episodes-list');
            list.innerHTML = '';
            
            if (episodes.length === 0) {
                list.innerHTML = '<div class="text-muted">No recent episodes</div>';
                return;
            }

            episodes.slice(0, 5).forEach(ep => {
                let badgeClass = 'badge-primary';
                if (ep.status === 'mastered') badgeClass = 'badge-success';
                else if (ep.status === 'struggling') badgeClass = 'badge-warning';

                const html = `
                    <div class="episode-item">
                        <div class="episode-main">
                            <h4>${ep.topic}</h4>
                            <div class="episode-meta">
                                Duration: ${ep.duration_min}m &bull; Friction: ${ep.friction.toFixed(2)}
                            </div>
                        </div>
                        <div class="episode-status">
                            <span class="badge ${badgeClass}">${ep.status}</span>
                        </div>
                    </div>
                `;
                list.insertAdjacentHTML('beforeend', html);
            });
        }
    } catch (e) {
        console.error("Failed to load overview data:", e);
        if (window.Notifications) {
            window.Notifications.error("Connection Error", "Failed to load dashboard data from backend.");
        }
    }
});
