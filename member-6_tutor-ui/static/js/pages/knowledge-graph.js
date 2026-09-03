/**
 * Knowledge Graph D3 Visualization Logic
 */

let simulation = null;
let zoomBehavior = null;
let svg = null;
let g = null;

document.addEventListener('DOMContentLoaded', async () => {
    const loader = document.getElementById('kg-loader');
    try {
        const kgData = await window.API.getKnowledgeGraph();
        
        if (loader) {
            loader.classList.add('hidden');
        }
        
        if (!kgData || !kgData.nodes || !kgData.links) {
            throw new Error("Invalid Knowledge Graph data format");
        }
        
        renderGraph(kgData);
    } catch (e) {
        console.error("Failed to load Knowledge Graph:", e);
        if (loader) {
            loader.innerHTML = '<p class="text-muted">Failed to load Knowledge Graph. Please refresh.</p>';
        }
        if (window.Notifications) {
            window.Notifications.error("Visualization Error", "Failed to render the knowledge graph.");
        }
    }
});

function renderGraph(data) {
    const container = document.getElementById('d3-container');
    if (!container) return;
    
    // Clean up any existing SVG
    container.innerHTML = '';
    if (simulation) {
        simulation.stop();
        simulation = null;
    }

    const width = Math.max(container.clientWidth || 900, 600);
    const height = Math.max(container.clientHeight || 600, 500);
    
    if (typeof d3 === 'undefined') {
        container.innerHTML = '<p class="text-muted" style="padding: 20px;">D3 visualization library is initializing...</p>';
        return;
    }

    // Setup SVG
    svg = d3.select("#d3-container").append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", [0, 0, width, height]);
        
    g = svg.append("g");
    
    // Zoom Support
    zoomBehavior = d3.zoom()
        .scaleExtent([0.2, 4])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        });
        
    svg.call(zoomBehavior);
    
    // Color Scale based on status
    const color = (status) => {
        if (status === 'mastered' || status === 'strong') return 'var(--status-success, #10b981)';
        if (status === 'good' || status === 'developing') return 'var(--status-warning, #f59e0b)';
        return 'var(--status-danger, #ef4444)'; // weak
    };
    
    // Copy nodes and links to prevent mutating original data
    const nodes = data.nodes.map(d => ({
        ...d,
        confidence: typeof d.confidence === 'number' ? d.confidence : 0.5
    }));
    const links = data.links.map(d => ({ ...d }));

    // Simulation
    simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(110))
        .force("charge", d3.forceManyBody().strength(-350))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(d => 32 + d.confidence * 15));
        
    // Links (Edges)
    const link = g.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .join("line")
        .attr("stroke", "var(--border-secondary, #334155)")
        .attr("stroke-width", 2)
        .attr("stroke-opacity", 0.6);
        
    // Nodes
    const node = g.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(nodes)
        .join("g")
        .style("cursor", "pointer")
        .call(drag(simulation));
        
    node.append("circle")
        .attr("r", d => 16 + d.confidence * 14)
        .attr("fill", d => color(d.status))
        .attr("stroke", "#0f172a")
        .attr("stroke-width", 2)
        .on("click", (event, d) => showNodeDetails(d));
        
    node.append("text")
        .attr("x", 22)
        .attr("y", "0.31em")
        .attr("fill", "var(--text-primary, #f8fafc)")
        .attr("font-size", "12px")
        .attr("font-family", "Inter, sans-serif")
        .text(d => d.label || d.id);
        
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
            
        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    });
    
    // Setup Controls
    const btnZoomIn = document.getElementById('btn-zoom-in');
    const btnZoomOut = document.getElementById('btn-zoom-out');
    const btnRecenter = document.getElementById('btn-recenter');

    if (btnZoomIn) {
        btnZoomIn.onclick = () => svg.transition().duration(300).call(zoomBehavior.scaleBy, 1.3);
    }
    if (btnZoomOut) {
        btnZoomOut.onclick = () => svg.transition().duration(300).call(zoomBehavior.scaleBy, 0.7);
    }
    if (btnRecenter) {
        btnRecenter.onclick = () => svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity);
    }
}

function showNodeDetails(d) {
    const panel = document.getElementById('node-panel');
    if (!panel) return;
    
    const badge = document.getElementById('node-status-badge');
    const fill = document.getElementById('node-confidence-fill');
    
    document.getElementById('node-title').textContent = d.label || d.id;
    
    const status = d.status || 'developing';
    badge.textContent = status.toUpperCase();
    badge.className = 'badge';
    
    let trackColor = 'var(--status-danger)';
    if (status === 'mastered' || status === 'strong') {
        badge.classList.add('badge-success');
        trackColor = 'var(--status-success)';
    } else if (status === 'good' || status === 'developing') {
        badge.classList.add('badge-warning');
        trackColor = 'var(--status-warning)';
    } else {
        badge.classList.add('badge-danger');
    }
    
    fill.style.width = `${Math.round((d.confidence || 0.5) * 100)}%`;
    fill.style.background = trackColor;
    
    panel.classList.remove('hidden');
}

// Drag behavior
function drag(sim) {
    function dragstarted(event) {
        if (!event.active) sim.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    function dragended(event) {
        if (!event.active) sim.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}
