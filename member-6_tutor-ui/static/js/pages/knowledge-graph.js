/**
 * Knowledge Graph D3 Visualization Logic
 */

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const kgData = await window.API.getKnowledgeGraph();
        
        // Hide loader
        document.getElementById('kg-loader').classList.add('hidden');
        
        if (!kgData || !kgData.nodes || !kgData.links) {
            throw new Error("Invalid KG Data");
        }
        
        renderGraph(kgData);
    } catch (e) {
        console.error("Failed to load KG:", e);
        if (window.Notifications) {
            window.Notifications.error("Visualization Error", "Failed to render the knowledge graph.");
        }
    }
});

let simulation, zoomBehavior, svg, g;

function renderGraph(data) {
    const container = document.getElementById('d3-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Setup SVG
    svg = d3.select("#d3-container").append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height]);
        
    g = svg.append("g");
    
    // Zoom Support
    zoomBehavior = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        });
        
    svg.call(zoomBehavior);
    
    // Color Scale based on status
    const color = (status) => {
        if (status === 'mastered' || status === 'strong') return 'var(--status-success)';
        if (status === 'good' || status === 'developing') return 'var(--status-warning)';
        return 'var(--status-danger)'; // weak
    };
    
    // Simulation
    simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(d => 30 + d.confidence * 20));
        
    // Links
    const link = g.append("g")
        .attr("class", "link")
        .selectAll("line")
        .data(data.links)
        .join("line")
        .attr("stroke-width", d => Math.sqrt(d.value));
        
    // Nodes
    const node = g.append("g")
        .attr("class", "node")
        .selectAll("g")
        .data(data.nodes)
        .join("g")
        .call(drag(simulation));
        
    node.append("circle")
        .attr("r", d => 15 + d.confidence * 15)
        .attr("fill", d => color(d.status))
        .on("click", (event, d) => showNodeDetails(d));
        
    node.append("text")
        .attr("x", 20)
        .attr("y", "0.31em")
        .text(d => d.id);
        
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
    document.getElementById('btn-zoom-in').addEventListener('click', () => {
        svg.transition().duration(300).call(zoomBehavior.scaleBy, 1.3);
    });
    document.getElementById('btn-zoom-out').addEventListener('click', () => {
        svg.transition().duration(300).call(zoomBehavior.scaleBy, 0.7);
    });
    document.getElementById('btn-recenter').addEventListener('click', () => {
        svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity);
    });
}

function showNodeDetails(d) {
    const panel = document.getElementById('node-panel');
    const badge = document.getElementById('node-status-badge');
    const fill = document.getElementById('node-confidence-fill');
    
    document.getElementById('node-title').textContent = d.id;
    
    badge.textContent = d.status.toUpperCase();
    badge.className = 'badge';
    
    let trackColor = 'var(--status-danger)';
    if (d.status === 'mastered' || d.status === 'strong') {
        badge.classList.add('badge-success');
        trackColor = 'var(--status-success)';
    }
    else if (d.status === 'good' || d.status === 'developing') {
        badge.classList.add('badge-warning');
        trackColor = 'var(--status-warning)';
    }
    else badge.classList.add('badge-danger');
    
    fill.style.width = `${d.confidence * 100}%`;
    fill.style.background = trackColor;
    
    panel.classList.remove('hidden');
}

// Drag behavior
function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}
