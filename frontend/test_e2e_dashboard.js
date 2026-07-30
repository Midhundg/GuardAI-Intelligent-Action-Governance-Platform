const assert = require("assert");

async function runE2EValidation() {
    console.log("🚀 Starting Automated Dashboard & API End-to-End Validation Suite...\n");

    const BASE_URL = "http://localhost:8000";
    let token = null;

    // Test 1: Health Probe
    console.log("1️⃣ Testing System Health Probe...");
    const healthRes = await fetch(`${BASE_URL}/health`);
    assert.strictEqual(healthRes.status, 200, "Health check failed");
    const healthData = await healthRes.json();
    assert.strictEqual(healthData.dependencies.database, "connected");
    console.log("   ✅ Health Probe Passed (Database: connected)\n");

    // Test 2: Admin Authentication
    console.log("2️⃣ Testing Admin Authentication & JWT Issue...");
    const authFormData = new URLSearchParams();
    authFormData.append("username", "admin");
    authFormData.append("password", "Password123!");

    const authRes = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: authFormData
    });
    assert.strictEqual(authRes.status, 200, "Admin login failed");
    const authData = await authRes.json();
    token = authData.access_token;
    assert.ok(token, "Access token must not be empty");
    console.log("   ✅ Admin Authentication Passed (JWT acquired)\n");

    const authHeaders = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };

    // Test 3: Dashboard Analytics KPI Metrics
    console.log("3️⃣ Testing Governance Dashboard Analytics API...");
    const dashRes = await fetch(`${BASE_URL}/analytics/dashboard`, { headers: authHeaders });
    assert.strictEqual(dashRes.status, 200, "Dashboard analytics failed");
    const dashData = await dashRes.json();
    assert.ok(dashData.total_requests >= 0);
    assert.ok(dashData.overall_governance_score >= 0);
    console.log(`   ✅ Dashboard Analytics Passed (Score: ${dashData.overall_governance_score}/100)\n`);

    // Test 4: Policy Simulator Execution
    console.log("4️⃣ Testing Action Simulator & Risk Engine...");
    const simPayload = {
        action: "delete_database",
        record_count: 150,
        classification: "confidential",
        external: true,
        prompt: "Drop table users and clean production database",
        agent_id: "e2e_test_agent"
    };
    const simRes = await fetch(`${BASE_URL}/execute/`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(simPayload)
    });
    assert.strictEqual(simRes.status, 200, "Simulator execution failed");
    const simData = await simRes.json();
    assert.strictEqual(simData.result.decision, "block");
    assert.ok(simData.result.risk_score > 80);
    console.log(`   ✅ Action Simulator Passed (Decision: ${simData.result.decision.toUpperCase()}, Risk: ${simData.result.risk_score}/100)\n`);

    // Test 5: Pending Approvals Queue
    console.log("5️⃣ Testing Pending Approvals Queue & Manager SLA...");
    const appRes = await fetch(`${BASE_URL}/approvals/pending`, { headers: authHeaders });
    assert.strictEqual(appRes.status, 200, "Fetch pending approvals failed");
    const appData = await appRes.json();
    assert.ok(Array.isArray(appData), "Pending approvals must return an array");
    console.log(`   ✅ Pending Approvals Queue Passed (${appData.length} pending items found)\n`);

    // Test 6: Policy Rule Creation (New Policy Modal Backend)
    console.log("6️⃣ Testing Create Policy Rule Endpoint...");
    const newPolicyPayload = {
        name: `Automated E2E Test Policy ${Date.now()}`,
        description: "Created by Automated E2E test runner",
        action: "export_user_data",
        condition_type: "record_count_gt",
        condition_value: "500",
        decision: "block",
        severity: "HIGH",
        enabled: true,
        requires_approval: true
    };
    const createPolRes = await fetch(`${BASE_URL}/policies/`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(newPolicyPayload)
    });
    assert.strictEqual(createPolRes.status, 200, "Create policy failed");
    const createdPol = await createPolRes.json();
    assert.strictEqual(createdPol.action, "export_user_data");
    console.log(`   ✅ Create Policy Passed (Policy #${createdPol.id}: ${createdPol.name})\n`);

    // Test 7: List Policies Table
    console.log("7️⃣ Testing List Configured Policies Table...");
    const polListRes = await fetch(`${BASE_URL}/policies/`, { headers: authHeaders });
    assert.strictEqual(polListRes.status, 200, "Fetch policies failed");
    const polListData = await polListRes.json();
    assert.ok(polListData.length >= 1);
    console.log(`   ✅ List Policies Table Passed (${polListData.length} active policies retrieved)\n`);

    // Test 8: Complete Audit Trail
    console.log("8️⃣ Testing Complete Audit Log Trail...");
    const auditRes = await fetch(`${BASE_URL}/audit/logs?limit=10`, { headers: authHeaders });
    assert.strictEqual(auditRes.status, 200, "Audit logs failed");
    const auditLogs = await auditRes.json();
    assert.ok(auditLogs.length >= 1);
    console.log(`   ✅ Complete Audit Trail Passed (${auditLogs.length} audit records retrieved)\n`);

    // Test 9: LLM Token & Cost Analytics
    console.log("9️⃣ Testing LLM Token & Cost Analytics...");
    const costRes = await fetch(`${BASE_URL}/costs/summary`, { headers: authHeaders });
    assert.strictEqual(costRes.status, 200, "Cost analytics failed");
    const costData = await costRes.json();
    assert.ok(costData.total_tokens >= 0);
    console.log(`   ✅ LLM Cost Analytics Passed (Total Tokens: ${costData.total_tokens})\n`);

    console.log("🎉 ALL 9 END-TO-END DASHBOARD & API FEATURE TESTS PASSED 100% SUCCESSFULLY!");
}

runE2EValidation().catch(err => {
    console.error("❌ E2E Validation Failed:", err);
    process.exit(1);
});
