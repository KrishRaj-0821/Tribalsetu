// TribalSetu Frontend JavaScript Engine

let currentVerificationResult = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSchemes();
    loadOfficerDashboard();
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabId).style.display = 'block';
    event.currentTarget.classList.add('active');

    if (tabId === 'officer-view') {
        loadOfficerDashboard();
    }
}

async function loadSchemes() {
    try {
        const res = await fetch('/api/schemes');
        const data = await res.json();
        const select = document.getElementById('scheme-select');
        select.innerHTML = '';
        data.schemes.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.name;
            select.appendChild(opt);
        });
        updateSchemeDetails(data.schemes[0]);
        select.addEventListener('change', () => {
            const selected = data.schemes.find(s => s.id === select.value);
            updateSchemeDetails(selected);
        });
    } catch (e) {
        console.error('Error loading schemes:', e);
    }
}

function updateSchemeDetails(scheme) {
    if (!scheme) return;
    document.getElementById('scheme-amount').textContent = scheme.award_amount;
    document.getElementById('scheme-deadline').textContent = scheme.deadline;
    document.getElementById('scheme-income').textContent = `Max ₹${scheme.income_limit.toLocaleString('en-IN')}/year`;
    
    const docList = document.getElementById('scheme-docs');
    docList.innerHTML = '';
    scheme.required_documents.forEach(d => {
        const li = document.createElement('li');
        li.textContent = d;
        docList.appendChild(li);
    });
}

// 1-Click Sample Document Loaders
async function loadSample(sampleName, name, caste, aadhaar, father) {
    document.getElementById('app-name').value = name;
    document.getElementById('app-caste').value = caste;
    document.getElementById('app-aadhaar').value = aadhaar;
    document.getElementById('app-father').value = father;

    try {
        const res = await fetch(`/api/sample-docs/${sampleName}`);
        const blob = await res.blob();
        const file = new File([blob], sampleName, { type: 'image/jpeg' });

        const container = new DataTransfer();
        container.items.add(file);
        document.getElementById('caste-file').files = container.files;

        // Preview image
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('cert-preview').src = e.target.result;
            document.getElementById('cert-preview-box').style.display = 'block';
        };
        reader.readAsDataURL(file);

        // Instant Verification
        runVerification();
    } catch (e) {
        alert('Could not load sample: ' + e);
    }
}

async function runVerification() {
    const fileInput = document.getElementById('caste-file');
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select or upload a certificate image!');
        return;
    }

    const btn = document.getElementById('btn-verify');
    btn.textContent = '⏳ Analyzing Forensics & Cryptography...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('caste_doc', fileInput.files[0]);
    formData.append('applicant_name', document.getElementById('app-name').value || 'Rahul Munda');
    formData.append('aadhaar_no', document.getElementById('app-aadhaar').value || '987654321012');
    formData.append('caste_name', document.getElementById('app-caste').value || 'Munda');
    formData.append('father_name', document.getElementById('app-father').value || 'Birsa Munda');
    formData.append('state', document.getElementById('app-state').value || 'jharkhand');

    try {
        const res = await fetch('/api/verify', {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        currentVerificationResult = result;
        displayVerificationResult(result);
    } catch (e) {
        alert('Verification failed: ' + e);
    } finally {
        btn.textContent = '🚀 Run 8-Layer AI Verification';
        btn.disabled = false;
    }
}

function displayVerificationResult(res) {
    document.getElementById('verification-results').style.display = 'block';

    const badge = document.getElementById('result-badge');
    badge.style.background = res.badge_color;
    badge.textContent = `${res.decision} - ${res.decision_label} (${res.trust_score}%)`;

    document.getElementById('result-summary').textContent = res.summary;

    // Display Heatmap
    if (res.ela_forensics.heatmap_base64) {
        document.getElementById('ela-heatmap-img').src = res.ela_forensics.heatmap_base64;
        document.getElementById('ela-heatmap-box').style.display = 'block';
    }
    document.getElementById('ela-status-text').textContent = res.ela_forensics.explanation;

    // Audit Trail
    const trailBox = document.getElementById('audit-trail-list');
    trailBox.innerHTML = '';
    res.audit_trail.forEach(item => {
        const div = document.createElement('div');
        div.className = 'audit-item ' + (item.includes('✓') ? 'success' : (item.includes('✗') ? 'danger' : 'warning'));
        div.textContent = item;
        trailBox.appendChild(div);
    });

    document.getElementById('btn-submit-app').style.display = 'block';
}

async function submitApplication() {
    if (!currentVerificationResult) return;

    const r = currentVerificationResult;
    const formData = new FormData();
    formData.append('applicant_name', r.applicant_name);
    formData.append('father_name', document.getElementById('app-father').value);
    formData.append('aadhaar_no', document.getElementById('app-aadhaar').value);
    formData.append('caste', r.verified_tribe);
    formData.append('state', r.state);
    formData.append('district', 'Hazaribagh');
    formData.append('scheme_name', document.getElementById('scheme-select').selectedOptions[0].text);
    formData.append('trust_score', r.trust_score);
    formData.append('decision', r.decision);
    formData.append('decision_label', r.decision_label);
    formData.append('badge_color', r.badge_color);
    formData.append('ela_tampering', r.ela_forensics.explanation);
    formData.append('audit_trail_json', JSON.stringify(r.audit_trail));

    try {
        const res = await fetch('/api/apply', { method: 'POST', body: formData });
        const data = await res.json();
        alert(`🎉 Application Successfully Submitted!\nTracking ID: ${data.application_id}\nStatus: ${data.application.status}`);
        document.getElementById('btn-submit-app').style.display = 'none';
        loadOfficerDashboard();
    } catch (e) {
        alert('Submission failed: ' + e);
    }
}

async function loadOfficerDashboard() {
    try {
        const res = await fetch('/api/applications');
        const data = await res.json();

        document.getElementById('kpi-total').textContent = data.total;
        document.getElementById('kpi-green').textContent = data.green_count;
        document.getElementById('kpi-yellow').textContent = data.yellow_count;
        document.getElementById('kpi-red').textContent = data.red_count;

        const tbody = document.getElementById('officer-table-body');
        tbody.innerHTML = '';

        const all = [...data.green_queue, ...data.yellow_queue, ...data.red_queue];
        all.forEach(app => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${app.id}</strong></td>
                <td>${app.applicant_name}</td>
                <td>${app.caste} (${app.state})</td>
                <td><span class="tag tag-${app.decision.toLowerCase()}">${app.trust_score}%</span></td>
                <td><span class="tag tag-${app.decision.toLowerCase()}">${app.decision_label}</span></td>
                <td>${app.status === 'APPROVED' ? '🟢 Paid via DBT' : '🟡 ' + app.status}</td>
                <td>
                    ${app.status !== 'APPROVED' && app.decision !== 'RED' 
                        ? `<button class="btn-approve" onclick="approveApp('${app.id}')">Approve & Pay DBT</button>` 
                        : `<span style="font-size: 11px; color:#64748B;">Completed</span>`}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error('Error loading officer dashboard:', e);
    }
}

async function approveApp(appId) {
    try {
        const res = await fetch(`/api/approve/${appId}`, { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        loadOfficerDashboard();
    } catch (e) {
        alert('Approval failed: ' + e);
    }
}
