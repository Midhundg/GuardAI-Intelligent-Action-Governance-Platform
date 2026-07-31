document.addEventListener("DOMContentLoaded", () => {
    // ----------------------------------------------------
    // State & API base
    // ----------------------------------------------------
    // Dynamic API URL for localhost, Vercel, or EC2
    const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://localhost:8000"
        : window.location.hostname.includes("vercel.app") 
            ? "https://guardai-backend-m4q5.onrender.com"
            : `http://${window.location.hostname}:8000`;
    let authToken = null;
    let riskChart = null;
    let violationChart = null;

    // ----------------------------------------------------
    // Tab Navigation
    // ----------------------------------------------------
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");

    const tabTitles = {
        overview: "Enterprise AI Governance Dashboard",
        approvals: "Manager Approval Queue",
        policies: "Configured Enterprise Policies",
        audit: "Complete Governance Audit Log Trail",
        costs: "Token & Cost Analytics"
    };

    const tabSubtitles = {
        overview: "Real-time Policy Enforcement, Autonomous Risk Scoring & Multi-Agent Gatekeeper",
        approvals: "High-risk AI actions requiring human-in-the-loop validation before execution",
        policies: "Manage declarative security constraints, threshold rules, and enforcement actions",
        audit: "Complete historical audit log of every evaluated action, risk score, and matched rule",
        costs: "Track LLM token consumption, cost metrics, and provider usage trends"
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const tabName = item.getAttribute("data-tab");
            navItems.forEach(n => n.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            item.classList.add("active");
            document.getElementById(`tab-${tabName}`).classList.add("active");
            pageTitle.textContent = tabTitles[tabName] || "GuardAI Enterprise";
            const sub = document.querySelector(".page-title-banner .subtitle");
            if (sub) sub.textContent = tabSubtitles[tabName] || "";

            // Load data for selected tab
            loadTabData(tabName);
        });
    });

    // ----------------------------------------------------
    // Initial Load & Auth Setup
    // ----------------------------------------------------
    async function init() {
        await loginDefaultAdmin();
        initCharts();
        loadDashboardData();
        setupWebSocket();
    }

    async function loginDefaultAdmin() {
        const select = document.getElementById("user-switcher-select");
        const currentUser = select ? select.value : "admin";
        await window.switchActiveUser(currentUser);
    }

    window.switchActiveUser = async function (username) {
        try {
            const formData = new URLSearchParams();
            formData.append("username", username || "admin");
            formData.append("password", "Password123!");

            const res = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                authToken = data.access_token;

                const roleTags = {
                    "admin": "ENTERPRISE ADMIN",
                    "manager_jane": "DEVOPS MANAGER",
                    "dev_alex": "ENGINEERING EMPLOYEE",
                    "auditor_bob": "COMPLIANCE AUDITOR"
                };

                const roleEl = document.getElementById("user-role-tag");
                if (roleEl) roleEl.textContent = roleTags[username] || "ENTERPRISE USER";

                const activeTab = document.querySelector(".nav-item.active")?.getAttribute("data-tab") || "overview";
                loadTabData(activeTab);
            } else {
                alert(`Failed to authenticate as ${username}.`);
            }
        } catch (e) {
            console.error("Error switching active user", e);
        }
    };

    function getAuthHeaders() {
        const headers = { "Content-Type": "application/json" };
        if (authToken) {
            headers["Authorization"] = `Bearer ${authToken}`;
        }
        return headers;
    }

    // ----------------------------------------------------
    // Tab Data Handlers
    // ----------------------------------------------------
    function loadTabData(tabName) {
        if (tabName === "overview") loadDashboardData();
        else if (tabName === "approvals") loadApprovals();
        else if (tabName === "policies") loadPolicies();
        else if (tabName === "audit") loadAuditLogs();
        else if (tabName === "costs") loadCosts();
    }

    // ----------------------------------------------------
    // 1. Dashboard Overview Data
    // ----------------------------------------------------
    async function loadDashboardData() {
        try {
            const res = await fetch(`${API_BASE}/analytics/dashboard`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();

                if (document.getElementById("kpi-total-requests")) document.getElementById("kpi-total-requests").textContent = data.total_requests || 0;
                if (document.getElementById("kpi-blocked-actions")) document.getElementById("kpi-blocked-actions").textContent = data.blocked_actions || 0;
                if (document.getElementById("kpi-pending-approvals")) document.getElementById("kpi-pending-approvals").textContent = data.pending_approvals || 0;
                if (document.getElementById("pending-badge")) document.getElementById("pending-badge").textContent = data.pending_approvals || 0;
                if (document.getElementById("kpi-avg-latency")) document.getElementById("kpi-avg-latency").textContent = `${data.average_latency_ms || 12.5} ms`;
            }

            // Violations
            const violRes = await fetch(`${API_BASE}/audit/most-violated-policies`, { headers: getAuthHeaders() });
            if (violRes.ok) {
                const violations = await violRes.json();
                updateViolationChart(violations);
            }

            // Audit Stream
            const auditRes = await fetch(`${API_BASE}/audit/logs?limit=8`, { headers: getAuthHeaders() });
            if (auditRes.ok) {
                const logs = await auditRes.json();
                renderOverviewAuditStream(logs);
            }
        } catch (e) {
            console.error("Error loading dashboard data", e);
        }
    }

    function renderOverviewAuditStream(logs) {
        const tbody = document.getElementById("overview-audit-body");
        if (!logs || logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No audit logs recorded yet. Run a simulation!</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${formatTime(log.timestamp)}</td>
                <td class="text-muted">${(log.request_id || "").substring(0, 8)}...</td>
                <td><strong>${log.action}</strong></td>
                <td><span class="pill pill-${log.risk_level || 'LOW'}">${log.risk_level || 'LOW'}</span></td>
                <td><span class="pill pill-${log.decision}">${log.decision}</span></td>
                <td class="text-muted">${log.reason || 'Completed'}</td>
            </tr>
        `).join("");
    }

    // ----------------------------------------------------
    // 2. Pending Approvals Queue
    // ----------------------------------------------------
    // ----------------------------------------------------
    // 2. Pending Approvals Queue
    // ----------------------------------------------------
    async function loadApprovals() {
        const container = document.getElementById("approvals-container");
        try {
            if (!authToken) await loginDefaultAdmin();
            let res = await fetch(`${API_BASE}/approvals/pending`, { headers: getAuthHeaders() });
            if (!res.ok) {
                await loginDefaultAdmin();
                res = await fetch(`${API_BASE}/approvals/pending`, { headers: getAuthHeaders() });
            }

            if (!res.ok) {
                container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-circle-check text-success" style="font-size: 1.6rem; margin-bottom: 0.5rem; display: block;"></i>No pending approvals requiring sign-off. All queues clear!</div>`;
                return;
            }

            const approvals = await res.json();
            const pendingCount = Array.isArray(approvals) ? approvals.length : 0;
            if (document.getElementById("pending-badge")) document.getElementById("pending-badge").textContent = pendingCount;
            if (document.getElementById("kpi-pending-approvals")) document.getElementById("kpi-pending-approvals").textContent = pendingCount;

            if (pendingCount === 0) {
                container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-circle-check text-success" style="font-size: 1.6rem; margin-bottom: 0.5rem; display: block;"></i>No pending approvals requiring sign-off. All queues clear!</div>`;
                return;
            }

            container.innerHTML = approvals.map(appr => `
                <div class="approval-item-card">
                    <div class="approval-item-header">
                        <span>Action: <strong>${appr.action}</strong></span>
                        <span class="pill pill-pending">${appr.status}</span>
                    </div>
                    <div class="approval-meta">
                        <div>Request ID: <code>${appr.request_id}</code></div>
                        <div>Requested By: User #${appr.requested_by}</div>
                        <div>Created: ${formatTime(appr.created_at)}</div>
                    </div>
                    <div class="approval-actions">
                        <button class="btn btn-primary btn-sm btn-approve" data-id="${appr.id}">
                            <i class="fa-solid fa-check"></i> Approve
                        </button>
                        <button class="btn btn-outline btn-sm btn-reject" data-id="${appr.id}">
                            <i class="fa-solid fa-xmark"></i> Reject
                        </button>
                    </div>
                </div>
            `).join("");

            // Add button handlers
            document.querySelectorAll(".btn-approve").forEach(b => {
                b.addEventListener("click", () => handleApprovalDecision(b.getAttribute("data-id"), "APPROVED"));
            });
            document.querySelectorAll(".btn-reject").forEach(b => {
                b.addEventListener("click", () => handleApprovalDecision(b.getAttribute("data-id"), "REJECTED"));
            });
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-circle-check text-success" style="font-size: 1.6rem; margin-bottom: 0.5rem; display: block;"></i>No pending approvals requiring sign-off. All queues clear!</div>`;
        }
    }

    async function handleApprovalDecision(approvalId, decision) {
        try {
            const res = await fetch(`${API_BASE}/approvals/${approvalId}/decide`, {
                method: "POST",
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    decision: decision,
                    reason: `Decided via Manager Dashboard UI`,
                    comment: "Verified authorization ticket."
                })
            });
            if (res.ok) {
                loadApprovals();
                loadDashboardData();
            } else {
                alert("Action failed. Manager role required.");
            }
        } catch (e) {
            alert("Error submitting approval decision.");
        }
    }

    // ----------------------------------------------------
    // 3. Simulator Form & Rich Result Card
    // ----------------------------------------------------
    const simForm = document.getElementById("simulator-form");
    if (simForm) {
        simForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                action: document.getElementById("sim-action").value,
                record_count: parseInt(document.getElementById("sim-records").value) || 0,
                external: document.getElementById("sim-external").value === "true",
                email_id: document.getElementById("sim-email").value || "",
                path: document.getElementById("sim-path").value || ""
            };
            const outputPanel = document.getElementById("sim-output-content");
            outputPanel.innerHTML = '<div style="color: var(--accent-sky);"><i class="fa-solid fa-spinner fa-spin"></i> Evaluating policy engine & risk scoring algorithms...</div>';

            try {
                if (!authToken) await loginDefaultAdmin();
                const res = await fetch(`${API_BASE}/execute/`, {
                    method: "POST",
                    headers: getAuthHeaders(),
                    body: JSON.stringify({
                        action: payload.action,
                        record_count: payload.record_count,
                        external: payload.external,
                        email_id: payload.email_id,
                        path: payload.path,
                        agent_id: "simulation_agent"
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    renderFormattedSimulationResult(outputPanel, data);
                    loadDashboardData();
                } else {
                    const err = await res.json();
                    outputPanel.innerHTML = `<div class="text-danger">Error (${res.status}): ${JSON.stringify(err, null, 2)}</div>`;
                }
            } catch (err) {
                outputPanel.innerHTML = `<div class="text-danger">Network error: ${err.message}</div>`;
            }
        });
    }

    function renderFormattedSimulationResult(container, data) {
        const result = data.result || {};
        const decision = (result.decision || data.status || "UNKNOWN").toUpperCase();
        const riskLevel = (result.risk_level || "LOW").toUpperCase();
        const riskScore = result.risk_score !== undefined ? result.risk_score : 0;
        const matchedPolicy = result.matched_policy_name || "None (Default Rule)";
        const reason = result.reason || "Action evaluated successfully.";
        const alternative = result.suggested_alternative || "No alternative needed.";
        const aiExplain = result.ai_explanation ? result.ai_explanation.why_decision_was_made : null;

        let pillClass = "pill-allow";
        if (decision === "BLOCKED" || decision === "BLOCK") pillClass = "pill-block";
        else if (decision === "PENDING_APPROVAL" || decision === "REQUIRE_APPROVAL" || decision === "HUMAN_REVIEW") pillClass = "pill-pending";

        container.innerHTML = `
            <div class="sim-card-body">
                <div class="sim-header-row">
                    <div>
                        <span class="sim-label">GOVERNANCE DECISION</span>
                        <div class="sim-decision-title"><span class="pill ${pillClass}">${decision}</span></div>
                    </div>
                </div>
            </div>
        `;
    }

    // ----------------------------------------------------
    // 4. Policies Table
    // ----------------------------------------------------
    async function loadPolicies() {
        const tbody = document.getElementById("policies-table-body");
        if (!tbody) return;
        try {
            if (!authToken) await loginDefaultAdmin();
            const res = await fetch(`${API_BASE}/policies/`, { headers: getAuthHeaders() });
            if (res.ok) {
                const policies = await res.json();
                if (policies.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No policies configured.</td></tr>`;
                    return;
                }
                tbody.innerHTML = policies.map(p => `
                    <tr>
                        <td>#${p.id}</td>
                        <td><strong>${p.name}</strong></td>
                        <td><code>${p.action}</code></td>
                        <td>${p.condition_type}</td>
                        <td>${p.condition_value}</td>
                        <td><span class="pill pill-${p.decision}">${p.decision}</span></td>
                        <td><span class="pill pill-${p.severity}">${p.severity}</span></td>
                        <td><span class="text-success">${p.enabled ? 'ACTIVE' : 'DISABLED'}</span></td>
                    </tr>
                `).join("");
            } else {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error loading policies (${res.status}).</td></tr>`;
            }
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Failed to connect to backend server.</td></tr>`;
        }
    }

    // ----------------------------------------------------
    // 5. Complete Audit Log Table
    // ----------------------------------------------------
    async function loadAuditLogs() {
        const tbody = document.getElementById("audit-table-body");
        if (!tbody) return;
        try {
            if (!authToken) await loginDefaultAdmin();
            const res = await fetch(`${API_BASE}/audit/logs?limit=50`, { headers: getAuthHeaders() });
            if (res.ok) {
                const logs = await res.json();
                if (logs.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No audit logs recorded yet.</td></tr>`;
                    return;
                }
                tbody.innerHTML = logs.map(l => `
                    <tr>
                        <td>#${l.id}</td>
                        <td>${formatTime(l.timestamp)}</td>
                        <td><strong>${l.action}</strong></td>
                        <td><span class="pill pill-${l.decision}">${l.decision}</span></td>
                        <td>${l.risk_score || 0}</td>
                        <td><span class="pill pill-${l.risk_level || 'LOW'}">${l.risk_level || 'LOW'}</span></td>
                        <td>${l.execution_time_ms ? l.execution_time_ms + ' ms' : 'N/A'}</td>
                        <td class="text-muted">${l.reason || ''}</td>
                    </tr>
                `).join("");
            }
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Failed to load audit trail.</td></tr>`;
        }
    }

    // ----------------------------------------------------
    // 6. Costs & Token Analytics
    // ----------------------------------------------------
    async function loadCosts() {
        try {
            if (!authToken) await loginDefaultAdmin();
            const res = await fetch(`${API_BASE}/costs/summary`, { headers: getAuthHeaders() });
            if (res.ok) {
                const data = await res.json();
                if (document.getElementById("cost-total-tokens")) document.getElementById("cost-total-tokens").textContent = (data.total_tokens || 0).toLocaleString();
                if (document.getElementById("cost-total-usd")) document.getElementById("cost-total-usd").textContent = `$${(data.total_cost_usd || 0).toFixed(4)}`;

                const tbody = document.getElementById("provider-costs-body");
                if (tbody) {
                    const provs = data.provider_breakdown || {};
                    const keys = Object.keys(provs);
                    if (keys.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted">No LLM token consumption recorded yet.</td></tr>`;
                    } else {
                        tbody.innerHTML = keys.map(p => `
                            <tr>
                                <td><strong>${p.toUpperCase()}</strong></td>
                                <td>${provs[p].tokens.toLocaleString()}</td>
                                <td class="text-success">$${provs[p].cost_usd.toFixed(4)}</td>
                            </tr>
                        `).join("");
                    }
                }
            }
        } catch (e) {
            console.error("Error loading cost data", e);
        }
    }

    // ----------------------------------------------------
    // Chart Initialization
    // ----------------------------------------------------
    function initCharts() {
        const ctxViol = document.getElementById("violationChart");
        if (ctxViol) {
            violationChart = new Chart(ctxViol, {
                type: "bar",
                data: {
                    labels: ["DB Purge Guard", "Bulk Export Limit", "External Access Guard"],
                    datasets: [{
                        label: "Violations Count",
                        data: [5, 3, 2],
                        backgroundColor: "#6366f1"
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: "#9ca3af" } }, y: { ticks: { color: "#9ca3af" } } } }
            });
        }
        const ctxLat = document.getElementById("latencyChart");
        if (ctxLat) {
            new Chart(ctxLat, {
                type: "line",
                data: {
                    labels: ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00"],
                    datasets: [{
                        label: "Policy Engine Latency (ms)",
                        data: [12, 15, 11, 14, 13, 12],
                        borderColor: "#10b981",
                        fill: false,
                        tension: 0.3
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: "#9ca3af" } }, y: { ticks: { color: "#9ca3af" } } } }
            });
        }
    }

    function updateViolationChart(violations) {
        if (!violationChart || !violations) return;
        violationChart.data.labels = violations.map(v => v.policy_name);
        violationChart.data.datasets[0].data = violations.map(v => v.violations);
        violationChart.update();
    }

    // ----------------------------------------------------
    // WebSocket Integration
    // ----------------------------------------------------
    function setupWebSocket() {
        try {
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const host = (window.location.port === "8000" || window.location.port === "") ? window.location.host : "localhost:8000";
            const ws = new WebSocket(`${protocol}//${host}/ws`);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.event === "audit_event" || data.event === "approval_created") {
                    loadDashboardData();
                }
            };
        } catch (e) {
            console.log("WebSocket fallback mode");
        }
    }

    function formatTime(isoStr) {
        if (!isoStr) return "N/A";
        try {
            const d = new Date(isoStr);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch (e) {
            return isoStr;
        }
    }

    // Global Search & Keyboard Shortcut (⌘K or '/')
    const searchInput = document.getElementById("global-search-input");
    if (searchInput) {
        document.addEventListener("keydown", (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                searchInput.focus();
            } else if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
                e.preventDefault();
                searchInput.focus();
            }
        });

        searchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll(".data-table tbody tr").forEach((row) => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? "" : "none";
            });
        });
    }

    document.getElementById("btn-refresh")?.addEventListener("click", () => {
        loadDashboardData();
        loadPolicies();
    });

    // Initialize application
    init();
});
