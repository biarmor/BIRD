// BIRD Client Application Logic

const API_BASE = window.location.origin;
let currentUser = null;
let currentWorkspaceId = "";
let workspaces = [];

// DOM Elements
const authContainer = document.getElementById("auth-container");
const appContainer = document.getElementById("app-container");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const authMessage = document.getElementById("auth-message");
const btnLogout = document.getElementById("btn-logout");
const userDisplayName = document.getElementById("user-display-name");
const workspaceSelect = document.getElementById("workspace-select");
const btnCreateWorkspace = document.getElementById("btn-create-workspace");

// View sections
const sidebarNav = document.querySelectorAll(".nav-item");
const contentViews = document.querySelectorAll(".content-view");
const currentViewTitle = document.getElementById("current-view-title");
const currentViewDesc = document.getElementById("current-view-desc");

// Form elements
const orchestratorForm = document.getElementById("orchestrator-form");
const queryInput = document.getElementById("query-input");
const executionMode = document.getElementById("execution-mode");
const executionMonitorBody = document.getElementById("execution-monitor-body");
const executionStatusBadge = document.getElementById("execution-status-badge");
const reasoningHistoryTable = document.getElementById("reasoning-history-table").querySelector("tbody");

// Vault elements
const ingestFactForm = document.getElementById("ingest-fact-form");
const factInput = document.getElementById("fact-input");
const factCategory = document.getElementById("fact-category");
const factSource = document.getElementById("fact-source");
const vaultSearchForm = document.getElementById("vault-search-form");
const vaultSearchQuery = document.getElementById("vault-search-query");
const vaultFactsTable = document.getElementById("vault-facts-table").querySelector("tbody");
const factCountBadge = document.getElementById("fact-count-badge");

// Campaign elements
const createCampaignForm = document.getElementById("create-campaign-form");
const campaignName = document.getElementById("campaign-name");
const campaignChannel = document.getElementById("campaign-channel");
const campaignBrief = document.getElementById("campaign-brief");
const campaignListContainer = document.getElementById("campaign-list-container");
const campaignAnalyticsSection = document.getElementById("campaign-analytics-section");
const analyticsCampaignName = document.getElementById("analytics-campaign-name");
const btnRefreshMetrics = document.getElementById("btn-refresh-metrics");

// Metrics counters
const valImpressions = document.getElementById("val-impressions");
const valClicks = document.getElementById("val-clicks");
const valConversions = document.getElementById("val-conversions");
const valRoi = document.getElementById("val-roi");
const barImpressions = document.getElementById("bar-impressions");
const barClicks = document.getElementById("bar-clicks");
const barConversions = document.getElementById("bar-conversions");
const valBarImpressions = document.getElementById("val-bar-impressions");
const valBarClicks = document.getElementById("val-bar-clicks");
const valBarConversions = document.getElementById("val-bar-conversions");

// Modal elements
const modalContainer = document.getElementById("modal-container");
const modalTitle = document.getElementById("modal-title");
const modalBody = document.getElementById("modal-body");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const btnModalSubmit = document.getElementById("btn-modal-submit");

let modalSubmitCallback = null;

// ============================================================================
// Core Session & Token management
// ============================================================================

function getHeaders() {
    const token = localStorage.getItem("token");
    return {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {})
    };
}

async function checkAuth() {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("userId");
    const username = localStorage.getItem("username");
    
    if (!token || !userId) {
        showAuthScreen();
        return;
    }

    try {
        // Simple verification request
        const res = await fetch(`${API_BASE}/api/v1/auth/me?user_id=${userId}`, {
            headers: getHeaders()
        });

        if (res.status === 200) {
            currentUser = await res.json();
            userDisplayName.textContent = currentUser.full_name || currentUser.username;
            showAppScreen();
            await loadWorkspaces();
        } else {
            clearSession();
            showAuthScreen();
        }
    } catch (err) {
        console.error("Auth check failed:", err);
        // Fallback to local storage variables to allow offline/local dev use
        if (username) {
            userDisplayName.textContent = username;
            showAppScreen();
            await loadWorkspaces();
        } else {
            showAuthScreen();
        }
    }
}

function clearSession() {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    localStorage.removeItem("username");
    currentUser = null;
    currentWorkspaceId = "";
}

function showAuthScreen() {
    authContainer.classList.remove("hidden");
    appContainer.classList.add("hidden");
    authMessage.classList.add("hidden");
}

function showAppScreen() {
    authContainer.classList.add("hidden");
    appContainer.classList.remove("hidden");
}

// ============================================================================
// Event Listeners for Authentication
// ============================================================================

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const usernameVal = document.getElementById("login-username").value;
    const passwordVal = document.getElementById("login-password").value;
    
    authMessage.classList.add("hidden");
    
    try {
        const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: usernameVal, password: passwordVal })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            localStorage.setItem("token", data.access_token);
            // Parse payload
            const payload = JSON.parse(atob(data.access_token.split(".")[1]));
            localStorage.setItem("userId", payload.user_id);
            localStorage.setItem("username", payload.username);
            
            await checkAuth();
        } else {
            authMessage.textContent = data.detail || "Authentication failed.";
            authMessage.classList.remove("hidden", "success");
        }
    } catch (err) {
        authMessage.textContent = "Unable to connect to server.";
        authMessage.classList.remove("hidden", "success");
    }
});

registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const usernameVal = document.getElementById("reg-username").value;
    const emailVal = document.getElementById("reg-email").value;
    const fullnameVal = document.getElementById("reg-fullname").value;
    const passwordVal = document.getElementById("reg-password").value;

    authMessage.classList.add("hidden");

    try {
        const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: usernameVal,
                email: emailVal,
                password: passwordVal,
                full_name: fullnameVal || null
            })
        });

        const data = await res.json();

        if (res.ok) {
            authMessage.textContent = "Registration successful! You can now sign in.";
            authMessage.classList.add("success");
            authMessage.classList.remove("hidden");
            registerForm.reset();
        } else {
            authMessage.textContent = data.detail || "Registration failed.";
            authMessage.classList.remove("hidden", "success");
        }
    } catch (err) {
        authMessage.textContent = "Error communicating with server.";
        authMessage.classList.remove("hidden", "success");
    }
});

btnLogout.addEventListener("click", () => {
    clearSession();
    showAuthScreen();
});

// ============================================================================
// Workspace Routing & Management
// ============================================================================

async function loadWorkspaces() {
    try {
        const res = await fetch(`${API_BASE}/api/v1/workspaces/`, {
            headers: getHeaders()
        });
        workspaces = await res.json();
        
        // If no workspaces exist, create a default one
        if (workspaces.length === 0) {
            await createDefaultWorkspace();
            return;
        }

        renderWorkspaceOptions();
    } catch (err) {
        console.error("Failed to load workspaces:", err);
    }
}

async function createDefaultWorkspace() {
    try {
        const userId = localStorage.getItem("userId");
        const res = await fetch(`${API_BASE}/api/v1/workspaces/?owner_id=${userId}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                name: "Corporate Intelligence",
                description: "Primary workspace for competitor benchmarking"
            })
        });
        if (res.ok) {
            await loadWorkspaces();
        }
    } catch (err) {
        console.error("Failed to create default workspace:", err);
    }
}

function renderWorkspaceOptions() {
    workspaceSelect.innerHTML = "";
    workspaces.forEach(ws => {
        const opt = document.createElement("option");
        opt.value = ws.id;
        opt.textContent = ws.name;
        workspaceSelect.appendChild(opt);
    });

    if (workspaces.length > 0) {
        if (!currentWorkspaceId || !workspaces.find(w => w.id === currentWorkspaceId)) {
            currentWorkspaceId = workspaces[0].id;
        }
        workspaceSelect.value = currentWorkspaceId;
        onWorkspaceChanged();
    }
}

workspaceSelect.addEventListener("change", (e) => {
    currentWorkspaceId = e.target.value;
    onWorkspaceChanged();
});

function onWorkspaceChanged() {
    // Reload items for active view
    const activeView = document.querySelector(".content-view.active").id;
    if (activeView === "view-control-room") {
        loadReasoningHistory();
    } else if (activeView === "view-smart-vault") {
        loadVaultFacts();
    } else if (activeView === "view-campaign-center") {
        loadCampaigns();
    }
}

btnCreateWorkspace.addEventListener("click", () => {
    showModal("Create Workspace", `
        <div class="form-group">
            <label for="new-ws-name">Workspace Name</label>
            <input type="text" id="new-ws-name" placeholder="e.g. Q3 Launch Strategy" required>
        </div>
        <div class="form-group">
            <label for="new-ws-desc">Description</label>
            <textarea id="new-ws-desc" placeholder="Details about this workspace" rows="3"></textarea>
        </div>
    `, async () => {
        const nameVal = document.getElementById("new-ws-name").value;
        const descVal = document.getElementById("new-ws-desc").value;
        const userId = localStorage.getItem("userId");
        
        if (!nameVal) return;

        const res = await fetch(`${API_BASE}/api/v1/workspaces/?owner_id=${userId}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                name: nameVal,
                description: descVal
            })
        });

        if (res.ok) {
            await loadWorkspaces();
            hideModal();
        }
    });
});

// ============================================================================
// View Swapping (SPA Navigation)
// ============================================================================

sidebarNav.forEach(item => {
    item.addEventListener("click", (e) => {
        e.preventDefault();
        
        // Remove active class from nav items
        sidebarNav.forEach(i => i.classList.remove("active"));
        item.classList.add("active");

        // Swap view viewport
        const targetViewId = item.getAttribute("data-target");
        contentViews.forEach(v => v.classList.remove("active"));
        document.getElementById(targetViewId).classList.add("active");

        // Update titles
        const viewLink = item.getAttribute("href");
        if (viewLink === "#control-room") {
            currentViewTitle.textContent = "Control Room";
            currentViewDesc.textContent = "Coordinate autonomous AI agents and run reasoning queries";
            loadReasoningHistory();
        } else if (viewLink === "#smart-vault") {
            currentViewTitle.textContent = "Smart Vault";
            currentViewDesc.textContent = "Manage long-term semantic memory and knowledge facts";
            loadVaultFacts();
        } else if (viewLink === "#campaign-center") {
            currentViewTitle.textContent = "Campaign Center";
            currentViewDesc.textContent = "Design, compile, and launch automated marketing campaigns";
            loadCampaigns();
        }
    });
});

// ============================================================================
// Modal utility functions
// ============================================================================

function showModal(title, bodyHtml, onSubmit) {
    modalTitle.textContent = title;
    modalBody.innerHTML = bodyHtml;
    modalSubmitCallback = onSubmit;
    modalContainer.classList.remove("hidden");
}

function hideModal() {
    modalContainer.classList.add("hidden");
    modalBody.innerHTML = "";
    modalSubmitCallback = null;
}

btnModalCancel.addEventListener("click", hideModal);
btnModalSubmit.addEventListener("click", () => {
    if (modalSubmitCallback) {
        modalSubmitCallback();
    }
});

// ============================================================================
// View 1: Control Room (Orchestration & Reasoning)
// ============================================================================

orchestratorForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const queryText = queryInput.value;
    const modeVal = executionMode.value;

    if (!currentWorkspaceId) {
        alert("Please select or create a workspace first.");
        return;
    }

    executionStatusBadge.textContent = "executing";
    executionStatusBadge.className = "badge badge-amber";
    executionMonitorBody.innerHTML = `
        <div class="loading-wrapper">
            <div class="spinner"></div>
            <p>Invoking orchestrator agent...</p>
            <span class="text-muted text-center" style="font-size:12px;">Query: "${queryText}"</span>
        </div>
    `;

    try {
        if (modeVal === "V1_CYCLE") {
            const workspaceIdInt = parseInt(currentWorkspaceId) || 1;
            const res = await fetch(`${API_BASE}/api/v1/intelligence/analyze`, {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({
                    query: queryText,
                    workspace_id: workspaceIdInt
                })
            });

            const data = await res.json();

            if (res.ok) {
                executionStatusBadge.textContent = "completed";
                executionStatusBadge.className = "badge badge-green";
                renderV1ExecutionResult(data);
                orchestratorForm.reset();
            } else {
                executionStatusBadge.textContent = "failed";
                executionStatusBadge.className = "badge badge-red";
                executionMonitorBody.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-triangle-exclamation empty-icon" style="color:var(--accent-red)"></i>
                        <h4>Execution Mismatch</h4>
                        <p class="text-muted">${data.detail || data.error || "An error occurred during analysis."}</p>
                    </div>
                `;
            }
        } else {
            let apiQueryMode = "orchestrator-worker";
            if (modeVal === "ADAPTIVE") apiQueryMode = "adaptive-planning";
            else if (modeVal === "SEQUENTIAL") apiQueryMode = "debate";

            const res = await fetch(`${API_BASE}/api/v2/intelligence/analyze`, {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({
                    query: queryText,
                    workspace_id: currentWorkspaceId,
                    mode: apiQueryMode
                })
            });

            const data = await res.json();

            if (res.ok) {
                executionStatusBadge.textContent = "completed";
                executionStatusBadge.className = "badge badge-green";
                renderExecutionResult(data);
                loadReasoningHistory();
                orchestratorForm.reset();
            } else {
                executionStatusBadge.textContent = "failed";
                executionStatusBadge.className = "badge badge-red";
                executionMonitorBody.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-triangle-exclamation empty-icon" style="color:var(--accent-red)"></i>
                        <h4>Execution Mismatch</h4>
                        <p class="text-muted">${data.detail || data.error || "An error occurred during analysis."}</p>
                    </div>
                `;
            }
        }
    } catch (err) {
        executionStatusBadge.textContent = "failed";
        executionStatusBadge.className = "badge badge-red";
        executionMonitorBody.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-circle-xmark empty-icon" style="color:var(--accent-red)"></i>
                <h4>Connection Interrupted</h4>
                <p class="text-muted">Could not connect to the BIRD FastAPI orchestration endpoint.</p>
            </div>
        `;
    }
});

async function renderExecutionResult(queryResponse) {
    executionMonitorBody.innerHTML = "";
    
    // Header Info
    const timeMs = queryResponse.execution_time_ms || 0;
    const header = document.createElement("div");
    header.className = "margin-bottom-sm";
    header.innerHTML = `
        <h4 style="font-size:14px;color:var(--text-secondary);">Query ID: <span class="text-muted">${queryResponse.id}</span></h4>
        <p style="font-size:12px;color:var(--text-muted);">Duration: ${timeMs}ms | Tokens: ${queryResponse.token_count || 'N/A'}</p>
    `;
    executionMonitorBody.appendChild(header);

    // Get the reasoning steps for this query
    try {
        const res = await fetch(`${API_BASE}/api/v2/intelligence/${queryResponse.id}/reasoning`, {
            headers: getHeaders()
        });
        
        if (res.ok) {
            const chain = await res.json();
            if (chain.steps && chain.steps.length > 0) {
                const stepsHeader = document.createElement("h4");
                stepsHeader.textContent = "Reasoning Step Traces";
                stepsHeader.className = "margin-top-sm";
                executionMonitorBody.appendChild(stepsHeader);

                chain.steps.forEach(step => {
                    const stepCard = document.createElement("div");
                    stepCard.className = "monitor-card";
                    
                    let badgeClass = "badge-indigo";
                    if (step.agent_type.toLowerCase().includes("vault")) badgeClass = "badge-green";
                    if (step.agent_type.toLowerCase().includes("forge")) badgeClass = "badge-amber";

                    stepCard.innerHTML = `
                        <div class="monitor-header">
                            <span class="monitor-agent-name">
                                <i class="fa-solid fa-robot"></i> ${step.agent_type}
                            </span>
                            <span class="badge ${badgeClass}">Step ${step.step_number}</span>
                        </div>
                        <div class="monitor-conclusion">
                            <p>${step.reasoning_text}</p>
                            ${step.evidence ? `<p class="text-muted" style="font-size:11px;margin-top:6px;"><i class="fa-solid fa-receipt"></i> Evidence: ${step.evidence}</p>` : ''}
                            <span class="text-muted" style="font-size:10px;">Confidence: ${(step.confidence * 100).toFixed(0)}%</span>
                        </div>
                    `;
                    executionMonitorBody.appendChild(stepCard);
                });
            }
        }
    } catch (err) {
        console.error("Failed to load reasoning steps:", err);
    }

    // Conclusion Card
    const finalResult = queryResponse.result || {};
    const conclusionCard = document.createElement("div");
    conclusionCard.className = "monitor-card margin-top-sm";
    
    let resultText = finalResult.conclusion || finalResult.result || JSON.stringify(finalResult);
    let confidenceVal = finalResult.confidence || 1.0;

    conclusionCard.innerHTML = `
        <h4 style="color:var(--secondary);"><i class="fa-solid fa-circle-check"></i> Final System Output</h4>
        <div class="monitor-conclusion success" style="margin-top:8px;">
            <p style="font-weight:500;">${resultText}</p>
            <p style="font-size:11px;color:var(--text-muted);margin-top:6px;">
                Confidence rating: <strong>${(confidenceVal * 100).toFixed(0)}%</strong>
            </p>
        </div>
    `;
    executionMonitorBody.appendChild(conclusionCard);
}


function renderV1ExecutionResult(response) {
    executionMonitorBody.innerHTML = "";

    // 1. Header Information
    const header = document.createElement("div");
    header.className = "margin-bottom-sm";
    header.innerHTML = `
        <h4 style="font-size:14px;color:var(--text-secondary);">Query: <span class="text-muted">${response.query}</span></h4>
        <p style="font-size:12px;color:var(--text-muted);">Timestamp: ${new Date(response.timestamp).toLocaleString()}</p>
    `;
    executionMonitorBody.appendChild(header);

    // 2. Thoughts Traces Card
    if (response.thoughts && response.thoughts.length > 0) {
        const thoughtsHeader = document.createElement("h4");
        thoughtsHeader.textContent = "Agent Thought Traces";
        thoughtsHeader.className = "margin-top-sm";
        executionMonitorBody.appendChild(thoughtsHeader);

        const thoughtsCard = document.createElement("div");
        thoughtsCard.className = "monitor-card";
        let thoughtsListHtml = response.thoughts.map(thought => `<li>${thought}</li>`).join("");
        thoughtsCard.innerHTML = `
            <div class="monitor-header">
                <span class="monitor-agent-name"><i class="fa-solid fa-brain"></i> Cognitive Steps</span>
                <span class="badge badge-indigo">Thoughts</span>
            </div>
            <div class="monitor-conclusion">
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.6; color: var(--text-secondary);">
                    ${thoughtsListHtml}
                </ul>
            </div>
        `;
        executionMonitorBody.appendChild(thoughtsCard);
    }

    // 3. Radar Summary Card
    if (response.radar_summary && response.radar_summary.top_results && response.radar_summary.top_results.length > 0) {
        const radarHeader = document.createElement("h4");
        radarHeader.textContent = "Radar Intelligence Gathering (Web Search)";
        radarHeader.className = "margin-top-sm";
        executionMonitorBody.appendChild(radarHeader);

        const radarCard = document.createElement("div");
        radarCard.className = "monitor-card";
        let resultsListHtml = response.radar_summary.top_results.map(r => `
            <div style="margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px;">
                <a href="${r.url}" target="_blank" style="color: var(--primary); font-weight: 600; text-decoration: none; font-size: 13px;">${r.title}</a>
                <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-muted);">${r.description}</p>
                <div style="margin-top: 4px; font-size: 10px; color: var(--text-secondary);">
                    <span class="badge badge-green" style="font-size: 9px; padding: 2px 4px;">Relevance: ${Math.round(r.relevance_score * 100)}%</span>
                    <span style="margin-left: 8px;"><i class="fa-solid fa-earth-americas"></i> ${r.source}</span>
                </div>
            </div>
        `).join("");
        radarCard.innerHTML = `
            <div class="monitor-header">
                <span class="monitor-agent-name"><i class="fa-solid fa-magnifying-glass"></i> RadarAgent</span>
                <span class="badge badge-green">${response.radar_summary.total_results} Results Found</span>
            </div>
            <div class="monitor-conclusion" style="max-height: 250px; overflow-y: auto;">
                ${resultsListHtml}
            </div>
        `;
        executionMonitorBody.appendChild(radarCard);
    }

    // 4. Final Reasoning Analysis Report Card
    if (response.analysis) {
        const reportHeader = document.createElement("h4");
        reportHeader.textContent = "Reasoning Analysis & Strategy";
        reportHeader.className = "margin-top-sm";
        executionMonitorBody.appendChild(reportHeader);

        const reportCard = document.createElement("div");
        reportCard.className = "monitor-card";
        
        let findingsHtml = (response.analysis.key_findings || []).map(f => `<li>${f}</li>`).join("");
        let nextStepsHtml = (response.analysis.next_steps || []).map(ns => `<li>${ns}</li>`).join("");

        reportCard.innerHTML = `
            <div class="monitor-header">
                <span class="monitor-agent-name"><i class="fa-solid fa-robot"></i> ReasoningAgent</span>
                <span class="badge badge-amber">Completed Report</span>
            </div>
            <div class="monitor-conclusion">
                <h5 style="color: var(--secondary); margin: 0 0 8px 0; font-size: 14px;">Summary</h5>
                <p style="margin: 0 0 16px 0; font-size: 13px; line-height: 1.6; white-space: pre-wrap;">${response.analysis.summary}</p>
                
                <h5 style="color: var(--secondary); margin: 0 0 8px 0; font-size: 14px;">Key Findings</h5>
                <ul style="margin: 0 0 16px 0; padding-left: 20px; font-size: 13px; line-height: 1.6;">
                    ${findingsHtml}
                </ul>

                <h5 style="color: var(--secondary); margin: 0 0 8px 0; font-size: 14px;">Full Intelligence Report</h5>
                <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px; font-size: 12.5px; line-height: 1.6; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; color: var(--text-secondary);">
                    ${response.analysis.full_analysis}
                </div>

                <h5 style="color: var(--secondary); margin: 16px 0 8px 0; font-size: 14px;">Next Strategic Steps</h5>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.6;">
                    ${nextStepsHtml}
                </ul>
            </div>
        `;
        executionMonitorBody.appendChild(reportCard);
    }
}


async function loadReasoningHistory() {
    if (!currentWorkspaceId) return;

    try {
        const res = await fetch(`${API_BASE}/api/v2/intelligence/?workspace_id=${currentWorkspaceId}`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const queries = await res.json();
            reasoningHistoryTable.innerHTML = "";

            if (queries.length === 0) {
                reasoningHistoryTable.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-muted">No reasoning chains saved yet.</td>
                    </tr>
                `;
                return;
            }

            queries.forEach(q => {
                const tr = document.createElement("tr");
                let conclusion = "Processing...";
                let confidence = "N/A";
                let hopsVal = "1";

                if (q.result) {
                    conclusion = q.result.conclusion || q.result.result || "Complete";
                    if (q.result.confidence !== undefined) {
                        confidence = `${(q.result.confidence * 100).toFixed(0)}%`;
                    }
                    if (q.result.hops !== undefined) {
                        hopsVal = q.result.hops;
                    }
                }

                // Truncate query and conclusion
                const shortQuery = q.query.length > 50 ? q.query.substring(0, 50) + "..." : q.query;
                const shortConclusion = conclusion.length > 60 ? conclusion.substring(0, 60) + "..." : conclusion;
                const dateStr = new Date(q.created_at).toLocaleString();

                tr.innerHTML = `
                    <td title="${q.query}"><strong>${shortQuery}</strong></td>
                    <td>${hopsVal}</td>
                    <td><span class="badge badge-indigo">${confidence}</span></td>
                    <td title="${conclusion}">${shortConclusion}</td>
                    <td class="text-muted" style="font-size:12px;">${dateStr}</td>
                `;
                reasoningHistoryTable.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Failed to load reasoning history:", err);
    }
}

// ============================================================================
// View 2: Smart Vault operations
// ============================================================================

ingestFactForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const factText = factInput.value;
    const catVal = factCategory.value;
    const srcVal = factSource.value;

    if (!currentWorkspaceId) {
        alert("Select workspace first.");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/v2/vault/facts?workspace_id=${currentWorkspaceId}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                fact: factText,
                category: catVal,
                source: srcVal,
                source_url: "",
                tags: [catVal]
            })
        });

        if (res.ok) {
            ingestFactForm.reset();
            loadVaultFacts();
        } else {
            const data = await res.json();
            alert("Error: " + (data.detail || "Unable to save fact."));
        }
    } catch (err) {
        console.error("Fact ingestion error:", err);
    }
});

vaultSearchForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const searchVal = vaultSearchQuery.value;

    if (!currentWorkspaceId) return;

    vaultFactsTable.innerHTML = `
        <tr>
            <td colspan="5" class="text-center">
                <div class="spinner" style="margin: 10px auto;"></div>
                Searching database...
            </td>
        </tr>
    `;

    try {
        const res = await fetch(`${API_BASE}/api/v2/vault/facts?workspace_id=${currentWorkspaceId}`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const facts = await res.json();
            // Filter locally on simple substring if search has content
            const filtered = facts.filter(f => 
                f.fact.toLowerCase().includes(searchVal.toLowerCase()) || 
                f.category.toLowerCase().includes(searchVal.toLowerCase())
            );

            renderVaultFactsList(filtered);
        }
    } catch (err) {
        console.error("Search failed:", err);
    }
});

async function loadVaultFacts() {
    if (!currentWorkspaceId) return;

    try {
        const res = await fetch(`${API_BASE}/api/v2/vault/facts?workspace_id=${currentWorkspaceId}`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const facts = await res.json();
            renderVaultFactsList(facts);
        }
    } catch (err) {
        console.error("Failed to load facts:", err);
    }
}

function renderVaultFactsList(facts) {
    vaultFactsTable.innerHTML = "";
    factCountBadge.textContent = `${facts.length} facts`;

    if (facts.length === 0) {
        vaultFactsTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">No facts stored in this workspace.</td>
            </tr>
        `;
        return;
    }

    facts.forEach(fact => {
        const tr = document.createElement("tr");
        const shortFact = fact.fact.length > 80 ? fact.fact.substring(0, 80) + "..." : fact.fact;

        tr.innerHTML = `
            <td title="${fact.fact}"><strong>${shortFact}</strong></td>
            <td><span class="badge badge-indigo">${fact.category}</span></td>
            <td class="text-muted">${fact.source || 'Manual'}</td>
            <td><span class="badge badge-green">${fact.confidence ? (fact.confidence * 100).toFixed(0) + '%' : '100%'}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="deleteFact('${fact.id}')" title="Delete Fact">
                    <i class="fa-solid fa-trash" style="color:var(--accent-red)"></i>
                </button>
            </td>
        `;
        vaultFactsTable.appendChild(tr);
    });
}

window.deleteFact = async function(factId) {
    if (!confirm("Are you sure you want to delete this fact from vector storage?")) return;

    try {
        const res = await fetch(`${API_BASE}/api/v2/vault/facts/${factId}`, {
            method: "DELETE",
            headers: getHeaders()
        });
        if (res.ok) {
            loadVaultFacts();
        }
    } catch (err) {
        console.error("Delete fact failed:", err);
    }
};

// ============================================================================
// View 3: Campaign Center operations
// ============================================================================

createCampaignForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nameVal = campaignName.value;
    const channelVal = campaignChannel.value;
    const briefVal = campaignBrief.value;

    if (!currentWorkspaceId) return;

    try {
        const res = await fetch(`${API_BASE}/api/v2/campaigns/`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                workspace_id: currentWorkspaceId,
                name: nameVal,
                target_channel: channelVal,
                budget: 1500.0,
                brief: briefVal
            })
        });

        if (res.ok) {
            createCampaignForm.reset();
            loadCampaigns();
        }
    } catch (err) {
        console.error("Campaign creation failed:", err);
    }
});

async function loadCampaigns() {
    if (!currentWorkspaceId) return;

    try {
        const res = await fetch(`${API_BASE}/api/v2/campaigns/?workspace_id=${currentWorkspaceId}`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const campaigns = await res.json();
            renderCampaignList(campaigns);
        }
    } catch (err) {
        console.error("Failed to load campaigns:", err);
    }
}

function renderCampaignList(campaigns) {
    campaignListContainer.innerHTML = "";
    
    if (campaigns.length === 0) {
        campaignListContainer.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-chart-line empty-icon"></i>
                <p>No campaigns found. Create a campaign to start deploying.</p>
            </div>
        `;
        campaignAnalyticsSection.style.display = "none";
        return;
    }

    campaigns.forEach(c => {
        const card = document.createElement("div");
        card.className = "campaign-card";
        
        let statusBadgeClass = "badge-indigo";
        if (c.status === "completed" || c.status === "deployed") statusBadgeClass = "badge-green";
        if (c.status === "failed") statusBadgeClass = "badge-red";

        card.innerHTML = `
            <div class="campaign-card-header">
                <h4>${c.name}</h4>
                <span class="badge ${statusBadgeClass}">${c.status}</span>
            </div>
            <p class="campaign-desc">${c.brief || 'No detailed brief provided.'}</p>
            <div style="font-size:12px;color:var(--text-muted);">
                <span>Channel: <strong>${c.target_channel}</strong></span>
            </div>
            <div class="campaign-actions">
                <button class="btn btn-secondary btn-sm" onclick="viewMetrics('${c.id}', '${c.name.replace(/'/g, "\\'")}')">
                    <i class="fa-solid fa-chart-simple"></i> View Analytics
                </button>
                ${c.status === "draft" ? `
                    <button class="btn btn-primary btn-sm" onclick="deployCampaign('${c.id}')">
                        <i class="fa-solid fa-rocket"></i> Deploy
                    </button>
                ` : ''}
            </div>
        `;
        campaignListContainer.appendChild(card);
    });
}

window.deployCampaign = async function(campaignId) {
    try {
        const res = await fetch(`${API_BASE}/api/v2/campaigns/${campaignId}/deploy`, {
            method: "POST",
            headers: getHeaders()
        });
        if (res.ok) {
            loadCampaigns();
            setTimeout(() => {
                viewMetrics(campaignId, "Campaign");
            }, 800);
        } else {
            alert("Deployment failed. Campaign agent returned error status.");
        }
    } catch (err) {
        console.error("Deploy failed:", err);
    }
};

let activeAnalyticsCampaignId = null;

window.viewMetrics = async function(campaignId, campaignNameVal) {
    activeAnalyticsCampaignId = campaignId;
    analyticsCampaignName.textContent = campaignNameVal;
    campaignAnalyticsSection.style.display = "block";
    
    // Scroll to analytics section
    campaignAnalyticsSection.scrollIntoView({ behavior: 'smooth' });

    await refreshCampaignMetrics();
};

btnRefreshMetrics.addEventListener("click", refreshCampaignMetrics);

async function refreshCampaignMetrics() {
    if (!activeAnalyticsCampaignId) return;

    try {
        const res = await fetch(`${API_BASE}/api/v2/campaigns/${activeAnalyticsCampaignId}/metrics`, {
            headers: getHeaders()
        });

        if (res.ok) {
            const metrics = await res.json();
            
            // Populate metrics counters
            valImpressions.textContent = metrics.impressions.toLocaleString();
            valClicks.textContent = metrics.clicks.toLocaleString();
            valConversions.textContent = metrics.conversions.toLocaleString();
            valRoi.textContent = `${metrics.roi.toFixed(1)}%`;

            // Calculate funnel bar graph percentages
            const maxVal = Math.max(metrics.impressions, 1);
            const clickPercent = (metrics.clicks / maxVal) * 100;
            const convPercent = (metrics.conversions / maxVal) * 100;

            barImpressions.style.width = "100%";
            barClicks.style.width = `${Math.max(clickPercent, 2)}%`;
            barConversions.style.width = `${Math.max(convPercent, 2)}%`;

            valBarImpressions.textContent = metrics.impressions.toLocaleString();
            valBarClicks.textContent = `${metrics.clicks.toLocaleString()} (${((metrics.clicks/maxVal)*100).toFixed(1)}%)`;
            valBarConversions.textContent = `${metrics.conversions.toLocaleString()} (${((metrics.conversions/maxVal)*100).toFixed(1)}%)`;
        }
    } catch (err) {
        console.error("Failed to refresh metrics:", err);
    }
}

// Initialize application
document.addEventListener("DOMContentLoaded", () => {
    checkAuth();
});
