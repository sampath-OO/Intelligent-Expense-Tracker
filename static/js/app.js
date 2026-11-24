// Intelligent Expense Tracker - Client Application Scripts

// Toast notification helper
function showToast(message, type = 'info', duration = 4000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div style="flex: 1;">${message}</div>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;">&times;</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.remove();
    }
  }, duration);
}

// Modal management
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Close modals when clicking outside modal-container or pressing Escape
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
  } else if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
    e.preventDefault();
    const searchInput = document.getElementById('liveSearchInput');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    } else {
      openModal('addTransactionModal');
    }
  }
});

// Category list for dynamic dropdowns
const CATEGORIES = [
  "Food & Dining",
  "Shopping & Retail",
  "Travel & Transport",
  "Personal & P2P Transfers",
  "Bills & Utilities",
  "Healthcare & Medical",
  "Education & Learning",
  "Entertainment & Recreation",
  "Allowances & Gifts",
  "Salary & Income",
  "General Expenses"
];

// PDF Statement Upload Handler
let extractedTransactions = [];

function initUploadPage() {
  const dropzone = document.getElementById('uploadDropzone');
  const fileInput = document.getElementById('pdfFileInput');
  const statusBox = document.getElementById('uploadStatusBox');
  const previewCard = document.getElementById('extractedPreviewCard');
  const previewBody = document.getElementById('extractedTableBody');
  const saveBtn = document.getElementById('saveExtractedBtn');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handlePdfFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handlePdfFile(fileInput.files[0]);
    }
  });

  function handlePdfFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showToast('Please select a valid PDF bank statement file.', 'error');
      return;
    }

    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileInfo').style.display = 'block';

    // Show processing animation
    statusBox.style.display = 'block';
    statusBox.innerHTML = `
      <div style="display:flex;align-items:center;gap:14px;padding:18px;background:#eff6ff;border-radius:12px;border:1px solid #bfdbfe;">
        <span class="spinner"></span>
        <div>
          <div style="font-weight:700;color:#1e3a8a;font-size:0.95rem;">Processing PDF Statement...</div>
          <div style="font-size:0.8rem;color:#475569;">Extracting transactions, dates, debits, credits, and AI contact classification...</div>
        </div>
      </div>
    `;

    const formData = new FormData();
    formData.append('statement', file);

    fetch('/api/extract-statement', {
      method: 'POST',
      body: formData
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        extractedTransactions = res.transactions;
        const meta = res.metadata || {};
        statusBox.innerHTML = `
          <div style="padding:16px 20px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
              <span style="font-weight:700; color:#166534; font-size:1rem;">✓ Statement Extraction Successful</span>
              <span class="badge badge-income">${extractedTransactions.length} Transactions Found</span>
            </div>
            <div style="display:flex; gap:20px; flex-wrap:wrap; font-size:0.84rem; color:#15803d; margin-top:6px;">
              <span><strong>Source:</strong> ${meta.provider || 'Digital Bank Statement'}</span>
              ${meta.account && meta.account !== 'N/A' ? `<span><strong>Account / ID:</strong> ${meta.account}</span>` : ''}
              ${meta.period && meta.period !== 'Current Cycle' ? `<span><strong>Cycle:</strong> ${meta.period}</span>` : ''}
            </div>
          </div>
        `;
        renderExtractedTable(extractedTransactions);
      } else {
        extractedTransactions = [];
        previewCard.style.display = 'none';
        
        let alertBg = res.is_scanned ? '#fffbeb' : '#fef2f2';
        let alertBorder = res.is_scanned ? '#fde68a' : '#fecaca';
        let alertColor = res.is_scanned ? '#92400e' : '#991b1b';

        statusBox.innerHTML = `
          <div style="padding:16px;background:${alertBg};border:1px solid ${alertBorder};border-radius:12px;color:${alertColor};">
            <h4 style="margin-bottom:6px;display:flex;align-items:center;gap:6px;">
              ${res.is_scanned ? 'ℹ️ Scanned PDF Notice' : '⚠️ Extraction Failed'}
            </h4>
            <p style="font-size:0.88rem;">${res.message}</p>
          </div>
        `;
      }
    })
    .catch(err => {
      statusBox.innerHTML = `
        <div style="padding:16px;background:#fef2f2;border:1px solid #fecaca;border-radius:12px;color:#991b1b;">
          Failed to process PDF statement: ${err.message}
        </div>
      `;
    });
  }

  function renderExtractedTable(txList) {
    previewBody.innerHTML = '';
    previewCard.style.display = 'block';
    document.getElementById('extractedCountBadge').textContent = `${txList.length} Extracted`;

    txList.forEach((tx, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="date" class="form-control form-control-sm" value="${tx.date}" onchange="updateExtractedField(${idx}, 'date', this.value)"></td>
        <td><input type="text" class="form-control form-control-sm" value="${escapeHtml(tx.description)}" onchange="updateExtractedField(${idx}, 'description', this.value)"></td>
        <td>
          <select class="form-control form-control-sm" onchange="updateExtractedField(${idx}, 'category', this.value)">
            ${CATEGORIES.map(c => `<option value="${c}" ${c === tx.category ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        </td>
        <td>
          <select class="form-control form-control-sm" onchange="updateExtractedField(${idx}, 'type', this.value)">
            <option value="expense" ${tx.type === 'expense' ? 'selected' : ''}>Expense (-)</option>
            <option value="income" ${tx.type === 'income' ? 'selected' : ''}>Income (+)</option>
          </select>
        </td>
        <td>
          <input type="number" step="0.01" class="form-control form-control-sm" value="${tx.amount}" onchange="updateExtractedField(${idx}, 'amount', parseFloat(this.value)||0)" style="text-align: right; font-weight: 700;">
        </td>
        <td style="text-align: center;">
          <button type="button" class="btn btn-sm btn-secondary" onclick="deleteExtractedRow(${idx})" title="Remove transaction" style="color: #ef4444; padding: 3px 8px;">&times;</button>
        </td>
      `;
      previewBody.appendChild(tr);
    });
  }

  window.updateExtractedField = function(idx, field, val) {
    if (extractedTransactions[idx]) {
      extractedTransactions[idx][field] = val;
    }
  };

  window.applyBulkCategory = function() {
    const bulkSelect = document.getElementById('bulkCategorySelect');
    if (!bulkSelect) return;
    const cat = bulkSelect.value;
    extractedTransactions.forEach(t => t.category = cat);
    renderExtractedTable(extractedTransactions);
    showToast(`All extracted rows assigned to '${cat}'`, 'info');
  };

  window.deleteExtractedRow = function(idx) {
    extractedTransactions.splice(idx, 1);
    renderExtractedTable(extractedTransactions);
  };

  saveBtn.addEventListener('click', () => {
    if (extractedTransactions.length === 0) {
      showToast('No transactions to save.', 'warning');
      return;
    }

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> Saving to Vault...';

    fetch('/api/save-extracted', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transactions: extractedTransactions })
    })
    .then(r => r.json())
    .then(res => {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Confirm & Save Transactions';
      if (res.success) {
        showToast(res.message, 'success');
        setTimeout(() => {
          window.location.href = '/transactions';
        }, 1200);
      } else {
        showToast(res.message, 'error');
      }
    })
    .catch(err => {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Confirm & Save Transactions';
      showToast('Failed to save transactions: ' + err.message, 'error');
    });
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Transaction Modal Edit / Delete handlers
function editTransaction(tx) {
  document.getElementById('editTxId').value = tx.id;
  document.getElementById('editTxDate').value = tx.date;
  document.getElementById('editTxDesc').value = tx.description;
  document.getElementById('editTxCategory').value = tx.category;
  document.getElementById('editTxType').value = tx.type;
  document.getElementById('editTxAmount').value = tx.amount;
  openModal('editTransactionModal');
}

function deleteTransactionConfirm(txId) {
  if (confirm('Are you sure you want to permanently delete this transaction?')) {
    fetch('/api/transaction/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: txId })
    })
    .then(r => r.json())
    .then(res => {
      if (res.success) {
        showToast('Transaction deleted successfully.', 'success');
        setTimeout(() => location.reload(), 600);
      } else {
        showToast(res.message || 'Error deleting transaction', 'error');
      }
    })
    .catch(err => showToast(err.message, 'error'));
  }
}

// Quick Budget Setter
function openBudgetModal(category, currentAmount, month) {
  document.getElementById('budgetCategory').value = category;
  document.getElementById('budgetAmount').value = currentAmount || '';
  document.getElementById('budgetMonth').value = month;
  document.getElementById('budgetModalTitle').textContent = `Set Budget for ${category}`;
  openModal('setBudgetModal');
}
