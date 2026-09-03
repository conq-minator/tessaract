/**
 * Overview Page Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch data concurrently
        const [context, sessionData, friction, episodes] = await Promise.all([
            window.API.getContext(),
            window.API.getSession(),
            window.API.getFriction(),
            window.API.getEpisodes()
        ]);

        // Render Context
        if (context) {
            const activeTools = Array.isArray(context.active_tools) && context.active_tools.length > 0 
                ? context.active_tools.join(', ') 
                : (context.application || 'System');
            document.getElementById('ui-subject').textContent = context.topic || context.subject || 'General';
            document.getElementById('ui-topic').textContent = context.intent ? `Intent: ${context.intent}` : (context.topic || 'No active topic');
            document.getElementById('ui-app').textContent = activeTools;
        }

        // Render Session
        if (sessionData) {
            const activeSession = sessionData.active_session || sessionData;
            const eventsCount = activeSession.events_count !== undefined 
                ? activeSession.events_count 
                : (activeSession.event_count || 0);
            
            let durationText = 'Just started';
            if (activeSession.start_time) {
                const startTime = new Date(activeSession.start_time);
                const now = new Date();
                const mins = Math.max(1, Math.round((now - startTime) / 60000));
                durationText = mins < 60 ? `${mins}m` : `${Math.floor(mins / 60)}h ${mins % 60}m`;
            }
            document.getElementById('ui-session-time').textContent = durationText;
            document.getElementById('ui-session-events').textContent = eventsCount;
        }

        // Render Friction
        if (friction) {
            const score = typeof friction.score === 'number' ? friction.score : 0;
            const fill = document.getElementById('ui-friction-fill');
            const badge = document.getElementById('ui-friction-badge');
            
            document.getElementById('ui-friction-score').textContent = score.toFixed(2);
            fill.style.width = `${Math.min(100, score * 100)}%`;
            
            const level = (friction.level || 'LOW').toUpperCase();
            badge.textContent = level;
            badge.className = 'badge'; // reset
            if (score > 0.7 || level === 'HIGH') badge.classList.add('badge-danger');
            else if (score > 0.3 || level === 'MEDIUM') badge.classList.add('badge-warning');
            else badge.classList.add('badge-success');
        }

        // Render Episodes
        if (episodes && Array.isArray(episodes)) {
            const list = document.getElementById('ui-episodes-list');
            list.innerHTML = '';
            
            if (episodes.length === 0) {
                list.innerHTML = '<div class="text-muted">No recent episodes recorded yet.</div>';
                return;
            }

            episodes.slice(0, 5).forEach(ep => {
                const fScore = typeof ep.friction_score === 'number' 
                    ? ep.friction_score 
                    : (typeof ep.friction === 'number' ? ep.friction : 0);
                const status = ep.outcome || ep.status || 'ongoing';
                const topic = ep.topic || 'General Activity';
                
                let badgeClass = 'badge-primary';
                if (status === 'mastered' || status === 'resolved') badgeClass = 'badge-success';
                else if (status === 'struggling' || fScore > 0.5) badgeClass = 'badge-warning';

                const html = `
                    <div class="episode-item">
                        <div class="episode-main">
                            <h4>${topic}</h4>
                            <div class="episode-meta">
                                Events: ${ep.events_count || ep.events || 1} &bull; Friction: ${fScore.toFixed(2)}
                            </div>
                        </div>
                        <div class="episode-status">
                            <span class="badge ${badgeClass}">${status}</span>
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
