const API_BASE = '/api';

document.addEventListener('DOMContentLoaded', () => {
  initTabNavigation();
  loadDashboard();
  setupFileInputListeners();
  setupInboundUpload();
  setupSkuUpload();
});

// Switch Navigasi Tab
function initTabNavigation() {
  const navItems = document.querySelectorAll('.nav-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetTab = item.dataset.tab;
      navItems.forEach(nav => nav.classList.remove('active'));
      tabPanes.forEach(pane => pane.classList.remove('active'));

      item.classList.add('active');
      document.getElementById(`tab-${targetTab}`).classList.add('active');

      if (targetTab === 'home') loadDashboard();
      if (targetTab === 'master') loadMasterSKU();
      if (targetTab === 'history') loadHistory();
    });
  });
}

function setupFileInputListeners() {
  const skuFile = document.getElementById('sku-file-input');
  const skuText = document.getElementById('sku-file-name');
  skuFile.addEventListener('change', () => {
    if (skuFile.files.length) skuText.innerText = skuFile.files[0].name;
  });

  const inbFile = document.getElementById('inbound-file-input');
  const inbText = document.getElementById('inbound-file-name');
  inbFile.addEventListener('change', () => {
    if (inbFile.files.length) inbText.innerText = inbFile.files[0].name;
  });
}

// Load Tab Home
async function loadDashboard() {
  try {
    const res = await fetch(`${API_BASE}/dashboard`);
    const data = await res.json();
    document.getElementById('dash-total-sku').innerText = data.total_sku || 0;
    document.getElementById('dash-total-history').innerText = data.total_history || 0;
    document.getElementById('dash-last-upload').innerText = data.last_upload_file || '-';
    document.getElementById('dash-last-time').innerText = data.last_upload_time || '-';
  } catch (err) {
    console.error("Gagal load dashboard", err);
  }
}

// Load Tab Master SKU
async function loadMasterSKU() {
  try {
    const res = await fetch(`${API_BASE}/sku`);
    const data = await res.json();
    const tbody = document.getElementById('sku-table-body');
    tbody.innerHTML = '';
    document.getElementById('master-total-items').innerText = data.total || 0;

    data.items.forEach(sku => {
      tbody.innerHTML += `
                <tr>
                    <td><strong>${sku.item_id}</strong></td>
                    <td>${sku.description}</td>
                    <td class="text-right">${sku.cpp}</td>
                </tr>`;
    });
  } catch (err) {
    console.error("Gagal load master SKU", err);
  }
}

// Process Upload Inbound Plan
function setupInboundUpload() {
  const btnProcess = document.getElementById('btn-process-inbound');
  const fileInput = document.getElementById('inbound-file-input');

  btnProcess.addEventListener('click', async () => {
    if (!fileInput.files.length) {
      alert('Pilih file Excel Inbound Plan terlebih dahulu!');
      return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    btnProcess.innerText = 'Processing...';
    btnProcess.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/inbound/process`, {
        method: 'POST',
        body: formData
      });
      const result = await res.json();

      if (res.ok) {
        renderInboundResult(result);
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (err) {
      alert('Gagal memproses file Inbound Plan.');
    } finally {
      btnProcess.innerText = 'Process';
      btnProcess.disabled = false;
    }
  });
}

function renderInboundResult(data) {
  document.getElementById('inbound-result-section').style.display = 'block';
  document.getElementById('res-total-sku').innerText = data.summary.total_sku;
  document.getElementById('res-total-qty').innerText = data.summary.total_qty_cs.toLocaleString();
  document.getElementById('res-total-pallets').innerText = data.summary.total_required_pallets.toLocaleString();

  const tbody = document.getElementById('inbound-result-tbody');
  tbody.innerHTML = '';
  data.items.forEach(row => {
    tbody.innerHTML += `
            <tr>
                <td>${row.container_number}</td>
                <td>${row.batch_number}</td>
                <td><strong>${row.item_id}</strong></td>
                <td>${row.description}</td>
                <td class="text-right">${row.cpp}</td>
                <td class="text-right">${row.qty_carton.toLocaleString()}</td>
                <td class="text-right"><strong>${row.qty_pallet}</strong></td>
            </tr>`;
  });

  document.getElementById('btn-download-result').onclick = () => {
    window.location.href = `${API_BASE}/history/${data.history_id}/export`;
  };
}

// Load Tab History
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/history`);
    const histories = await res.json();
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';

    if (!histories.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center">Belum ada riwayat upload.</td></tr>';
      return;
    }

    histories.forEach(h => {
      const isSuccess = h.status === 'Success';
      const badgeClass = isSuccess ? 'badge-success' : 'badge-danger';
      const actionButton = isSuccess
        ? `<button class="btn btn-secondary btn-sm" onclick="window.location.href='${API_BASE}/history/${h.history_id}/export'">Download</button>`
        : `<button class="btn btn-secondary btn-sm" onclick="alert('Proses upload ini gagal dan tidak memiliki detail data.')">View Error</button>`;

      tbody.innerHTML += `
        <tr>
            <td>${h.upload_time}</td>
            <td><strong>${h.file_name}</strong></td>
            <td class="text-center">${h.containers}</td>
            <td class="text-right">${h.total_qty_cs.toLocaleString()}</td>
            <td class="text-right"><strong>${h.required_pallets}</strong></td>
            <td><span class="badge ${badgeClass}">${h.status}</span></td>
            <td>${actionButton}</td>
        </tr>`;
    });
  } catch (err) {
    console.error("Gagal load history", err);
  }
}

// Upload Master SKU
function setupSkuUpload() {
  const btnReplace = document.getElementById('btn-replace-sku');
  const fileInput = document.getElementById('sku-file-input');

  btnReplace.addEventListener('click', async () => {
    if (!fileInput.files.length) {
      alert('Pilih file Excel Master SKU terlebih dahulu!');
      return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
      const res = await fetch(`${API_BASE}/sku/upload`, {
        method: 'POST',
        body: formData
      });
      const result = await res.json();
      if (res.ok) {
        alert(result.message);
        loadMasterSKU();
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (err) {
      alert('Gagal mengunggah file Master SKU.');
    }
  });
}