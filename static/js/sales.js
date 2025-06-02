// 全局变量
let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let currentStatusFilter = '';
let currentSearchQuery = '';
let currentUser = null;

// 初始化销售记录页面
async function initSalesPage() {
  // 获取当前用户
  currentUser = await getCurrentUser();
  if (!currentUser) return;
  
  // 加载销售记录列表
  loadSalesRecords();
  
  // 绑定新增按钮事件
  const addButton = document.getElementById('add-sales-btn');
  if (addButton) {
    addButton.addEventListener('click', showAddSalesModal);
  }
  
  // 绑定筛选表单提交事件
  const filterForm = document.getElementById('filter-form');
  if (filterForm) {
    filterForm.addEventListener('submit', handleFilterSubmit);
  }
  
  // 绑定状态筛选器更改事件
  const statusFilter = document.getElementById('status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', handleStatusFilterChange);
  }
  
  // 绑定分页事件
  const prevPageBtn = document.getElementById('prev-page');
  const nextPageBtn = document.getElementById('next-page');
  if (prevPageBtn && nextPageBtn) {
    prevPageBtn.addEventListener('click', handlePrevPage);
    nextPageBtn.addEventListener('click', handleNextPage);
  }
  
  // 绑定保存按钮事件
  const saveButton = document.getElementById('save-sales-btn');
  if (saveButton) {
    saveButton.addEventListener('click', handleSaveSales);
  }
  
  // 绑定删除确认按钮事件
  const confirmDeleteButton = document.getElementById('confirm-delete-btn');
  if (confirmDeleteButton) {
    confirmDeleteButton.addEventListener('click', handleDeleteSales);
  }
  
  // 绑定审核按钮事件
  const approveBtn = document.getElementById('approve-btn');
  const rejectBtn = document.getElementById('reject-btn');
  if (approveBtn && rejectBtn) {
    approveBtn.addEventListener('click', () => handleUpdateStatus('approved'));
    rejectBtn.addEventListener('click', () => handleUpdateStatus('rejected'));
  }
  
  // 检查URL参数，如果有id参数则打开对应记录详情
  checkUrlForRecordId();
}

// 检查URL是否包含记录ID参数
function checkUrlForRecordId() {
  const urlParams = new URLSearchParams(window.location.search);
  const recordId = urlParams.get('id');
  
  if (recordId) {
    // 延迟一小段时间确保页面已加载完成
    setTimeout(() => {
      showSalesDetails(recordId);
    }, 500);
  }
}

// 加载销售记录列表
async function loadSalesRecords() {
  try {
    // 构建查询参数
    const queryParams = new URLSearchParams({
      skip: (currentPage - 1) * pageSize,
      limit: pageSize
    });
    
    if (currentStatusFilter) {
      queryParams.append('status', currentStatusFilter);
    }
    
    if (currentSearchQuery) {
      queryParams.append('search', currentSearchQuery);
    }
    
    const records = await apiRequest(`/sales?${queryParams.toString()}`, { method: 'GET' });
    if (!records) return;
    
    // 更新总条数
    totalItems = records.length; // 假设返回的是列表，实际可能需要调整
    updatePagination();
    
    // 渲染表格
    renderSalesTable(records);
  } catch (error) {
    console.error('加载销售记录失败:', error);
    showToast('error', '加载销售记录失败，请稍后重试');
  }
}

// 渲染销售记录表格
function renderSalesTable(sales) {
  const tableBody = document.querySelector('#sales-table tbody');
  if (!tableBody) return;
  
  // 清空表格
  tableBody.innerHTML = '';
  
  if (!sales || sales.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `<td colspan="10" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  sales.forEach(sale => {
    // 权限控制：
    // - 超级管理员可以看到所有记录
    // - 高级用户可以看到自己和普通用户的记录
    // - 普通用户只能看到自己的记录
    if (currentUser.role === 'normal' && sale.user_id !== currentUser.id) {
      return;
    }
    if (currentUser.role === 'senior' && sale.user_id !== currentUser.id && sale.user.role !== 'normal') {
      return;
    }
    
    const row = document.createElement('tr');
    
    // 状态显示样式
    const statusClass = {
      'pending': 'text-warning',
      'approved': 'text-success',
      'rejected': 'text-danger'
    }[sale.status] || 'text-secondary';
    
    const statusText = {
      'pending': '待审核',
      'approved': '已审核',
      'rejected': '已拒绝'
    }[sale.status] || '未知';
    
    // 控制操作按钮显示 - 根据权限决定是否可以修改或删除
    // - 超级管理员可以修改和删除所有记录
    // - 高级用户可以修改和删除自己的记录和普通用户的记录
    // - 普通用户只能修改和删除自己的记录
    const canModify = currentUser.role === 'admin' || 
                     (currentUser.role === 'senior' && (sale.user_id === currentUser.id || sale.user.role === 'normal')) ||
                     (currentUser.role === 'normal' && sale.user_id === currentUser.id);
    
    // 控制审核按钮显示 - 只有高级用户和管理员可以审核
    const canApprove = currentUser.role !== 'normal' && sale.status === 'pending';
    
    // 格式化日期时间
    const formatDateTime = (dateStr) => {
      if (!dateStr) return '-';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    row.innerHTML = `
      <td>${sale.order_number}</td>
      <td>${sale.product_name}</td>
      <td>${sale.quantity}</td>
      <td>${sale.unit_price.toFixed(2)}</td>
      <td>${sale.total_amount.toFixed(2)}</td>
      <td>${sale.user ? sale.user.full_name : '-'}</td>
      <td><span class="${statusClass}">${statusText}</span></td>
      <td>${formatDateTime(sale.created_at)}</td>
      <td>${sale.created_by ? sale.created_by.full_name : '-'}</td>
      <td>${sale.approved_at ? formatDateTime(sale.approved_at) : '-'}</td>
      <td>${sale.approved_by ? sale.approved_by.full_name : '-'}</td>
      <td>
        <button class="btn btn-sm btn-info table-action-btn" onclick="showSalesDetails('${sale.order_number}')">
          <i class="bi bi-eye"></i> 查看
        </button>
        ${canModify ? `
          <button class="btn btn-sm btn-primary table-action-btn" onclick="showEditModal('${sale.order_number}')">
            <i class="bi bi-pencil"></i> 修改
          </button>
          <button class="btn btn-sm btn-danger table-action-btn" onclick="showDeleteModal('${sale.order_number}')">
            <i class="bi bi-trash"></i> 删除
          </button>
        ` : ''}
        ${canApprove ? `
          <button class="btn btn-sm btn-success table-action-btn" onclick="showApproveModal('${sale.order_number}')">
            <i class="bi bi-check-circle"></i> 审核
          </button>
        ` : ''}
      </td>
    `;
    
    tableBody.appendChild(row);
  });
}

// 更新分页信息
function updatePagination() {
  const paginationInfo = document.getElementById('pagination-info');
  const pagination = document.getElementById('pagination');
  const prevPageBtn = document.getElementById('prev-page');
  const nextPageBtn = document.getElementById('next-page');
  
  if (!paginationInfo || !pagination || !prevPageBtn || !nextPageBtn) return;
  
  // 计算分页信息
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const start = (currentPage - 1) * pageSize + 1;
  const end = Math.min(currentPage * pageSize, totalItems);
  
  // 更新分页信息文本
  paginationInfo.textContent = `显示 ${start} 到 ${end} 条数据，共 ${totalItems} 条`;
  
  // 更新上一页/下一页按钮状态
  prevPageBtn.parentElement.classList.toggle('disabled', currentPage === 1);
  nextPageBtn.parentElement.classList.toggle('disabled', currentPage === totalPages);
  
  // 移除现有的页码按钮
  const pageButtons = pagination.querySelectorAll('.page-item:not(:first-child):not(:last-child)');
  pageButtons.forEach(btn => btn.remove());
  
  // 添加页码按钮
  const maxPages = 5; // 最多显示的页码数
  let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
  let endPage = Math.min(totalPages, startPage + maxPages - 1);
  
  if (endPage - startPage + 1 < maxPages) {
    startPage = Math.max(1, endPage - maxPages + 1);
  }
  
  // 插入页码按钮
  const nextPageItem = nextPageBtn.parentElement;
  for (let i = startPage; i <= endPage; i++) {
    const pageItem = document.createElement('li');
    pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
    
    const pageLink = document.createElement('a');
    pageLink.className = 'page-link';
    pageLink.href = '#';
    pageLink.textContent = i;
    pageLink.addEventListener('click', (e) => {
      e.preventDefault();
      goToPage(i);
    });
    
    pageItem.appendChild(pageLink);
    pagination.insertBefore(pageItem, nextPageItem);
  }
}

// 跳转到指定页
function goToPage(page) {
  currentPage = page;
  loadSalesRecords();
}

// 处理上一页
function handlePrevPage(e) {
  e.preventDefault();
  if (currentPage > 1) {
    currentPage--;
    loadSalesRecords();
  }
}

// 处理下一页
function handleNextPage(e) {
  e.preventDefault();
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  if (currentPage < totalPages) {
    currentPage++;
    loadSalesRecords();
  }
}

// 处理筛选表单提交
function handleFilterSubmit(e) {
  e.preventDefault();
  currentSearchQuery = document.getElementById('search-input').value.trim();
  currentPage = 1; // 重置为第一页
  loadSalesRecords();
}

// 处理状态筛选器更改
function handleStatusFilterChange() {
  currentStatusFilter = document.getElementById('status-filter').value;
  currentPage = 1; // 重置为第一页
  loadSalesRecords();
}

// 显示新增销售记录模态框
function showAddSalesModal() {
  // 重置表单
  const form = document.getElementById('sales-form');
  if (form) {
    form.reset();
    form.classList.remove('was-validated');
  }
  
  // 设置模态框标题
  const modalTitle = document.getElementById('modal-title');
  if (modalTitle) {
    modalTitle.textContent = '新增销售记录';
  }
  
  // 清除记录ID
  const recordIdInput = document.getElementById('record-id');
  if (recordIdInput) {
    recordIdInput.value = '';
  }
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('sales-modal'));
  modal.show();
}

// 显示编辑销售记录模态框
async function showEditSalesModal(id) {
  try {
    // 获取记录详情
    const record = await apiRequest(`/sales/${id}`, { method: 'GET' });
    if (!record) return;
    
    // 重置表单
    const form = document.getElementById('sales-form');
    if (form) {
      form.reset();
      form.classList.remove('was-validated');
    }
    
    // 设置模态框标题
    const modalTitle = document.getElementById('modal-title');
    if (modalTitle) {
      modalTitle.textContent = '编辑销售记录';
    }
    
    // 设置记录ID
    const recordIdInput = document.getElementById('record-id');
    if (recordIdInput) {
      recordIdInput.value = id;
    }
    
    // 填充表单数据
    document.getElementById('order-number').value = record.order_number;
    document.getElementById('product-name').value = record.product_name;
    document.getElementById('quantity').value = record.quantity;
    document.getElementById('unit-price').value = record.unit_price;
    document.getElementById('shipping-fee').value = record.shipping_fee;
    document.getElementById('refund-amount').value = record.refund_amount;
    document.getElementById('tax-refund').value = record.tax_refund;
    document.getElementById('remarks').value = record.remarks || '';
    
    // 禁用订单编号字段（不允许修改）
    document.getElementById('order-number').disabled = true;
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('sales-modal'));
    modal.show();
  } catch (error) {
    console.error('获取销售记录详情失败:', error);
    showToast('error', '获取记录详情失败，请稍后重试');
  }
}

// 处理保存销售记录
async function handleSaveSales() {
  // 验证表单
  const form = document.getElementById('sales-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  // 获取表单数据
  const recordId = document.getElementById('record-id').value;
  const isEdit = !!recordId;
  
  const formData = {
    order_number: document.getElementById('order-number').value.trim(),
    product_name: document.getElementById('product-name').value.trim(),
    quantity: parseInt(document.getElementById('quantity').value),
    unit_price: parseFloat(document.getElementById('unit-price').value),
    shipping_fee: parseFloat(document.getElementById('shipping-fee').value) || 0,
    refund_amount: parseFloat(document.getElementById('refund-amount').value) || 0,
    tax_refund: parseFloat(document.getElementById('tax-refund').value) || 0,
    remarks: document.getElementById('remarks').value.trim() || null,
    // 创建人默认为当前用户
    created_by_id: currentUser.id
  };
  
  try {
    let response;
    
    if (isEdit) {
      // 更新现有记录
      response = await apiRequest(`/sales/${recordId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
    } else {
      // 创建新记录
      response = await apiRequest('/sales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
    }
    
    if (response) {
      // 隐藏模态框
      const modal = bootstrap.Modal.getInstance(document.getElementById('sales-modal'));
      modal.hide();
      
      // 显示成功消息
      showToast('success', isEdit ? '销售记录更新成功' : '销售记录创建成功');
      
      // 重新加载列表
      loadSalesRecords();
    }
  } catch (error) {
    console.error('保存销售记录失败:', error);
    showToast('error', '保存记录失败，请稍后重试');
  }
}

// 显示删除确认对话框
function showDeleteConfirm(id, orderNumber) {
  // 设置要删除的记录ID
  document.getElementById('delete-order-number').textContent = orderNumber;
  
  // 绑定删除按钮数据
  const confirmDeleteButton = document.getElementById('confirm-delete-btn');
  confirmDeleteButton.dataset.recordId = id;
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('delete-modal'));
  modal.show();
}

// 处理删除销售记录
async function handleDeleteSales() {
  const confirmDeleteButton = document.getElementById('confirm-delete-btn');
  const orderNumber = confirmDeleteButton.dataset.orderNumber;
  
  if (!orderNumber) return;
  
  try {
    const response = await apiRequest(`/sales/${orderNumber}`, { method: 'DELETE' });
    
    if (response) {
      // 隐藏模态框
      const modal = bootstrap.Modal.getInstance(document.getElementById('delete-modal'));
      modal.hide();
      
      // 显示成功消息
      showToast('success', '销售记录删除成功');
      
      // 重新加载列表
      loadSalesRecords();
    }
  } catch (error) {
    console.error('删除销售记录失败:', error);
    showToast('error', '删除记录失败，请稍后重试');
  }
}

// 显示销售记录详情
async function showSalesDetails(id, showApproveButtons = false) {
  try {
    // 获取记录详情
    const record = await apiRequest(`/sales/${id}`, { method: 'GET' });
    if (!record) return;
    
    // 格式化日期时间
    const formatDateTime = (dateStr) => {
      if (!dateStr) return '-';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    // 填充详情
    document.getElementById('detail-order-number').textContent = record.order_number;
    document.getElementById('detail-product-name').textContent = record.product_name;
    document.getElementById('detail-quantity').textContent = record.quantity;
    document.getElementById('detail-unit-price').textContent = parseFloat(record.unit_price).toFixed(2);
    document.getElementById('detail-shipping-fee').textContent = parseFloat(record.shipping_fee).toFixed(2);
    document.getElementById('detail-refund-amount').textContent = parseFloat(record.refund_amount).toFixed(2);
    document.getElementById('detail-tax-refund').textContent = parseFloat(record.tax_refund).toFixed(2);
    document.getElementById('detail-total-amount').textContent = parseFloat(record.total_amount).toFixed(2);
    document.getElementById('detail-creator').textContent = record.user ? record.user.full_name : '-';
    document.getElementById('detail-created-at').textContent = formatDateTime(record.created_at);
    document.getElementById('detail-created-by').textContent = record.created_by ? record.created_by.full_name : '-';
    document.getElementById('detail-approver').textContent = record.approved_by ? record.approved_by.full_name : '-';
    document.getElementById('detail-approved-at').textContent = record.approved_at ? formatDateTime(record.approved_at) : '-';
    document.getElementById('detail-remarks').textContent = record.remarks || '-';
    
    // 设置状态
    const statusElement = document.getElementById('detail-status');
    const statusClass = {
      'pending': 'text-warning',
      'approved': 'text-success',
      'rejected': 'text-danger'
    }[record.status] || 'text-secondary';
    
    const statusText = {
      'pending': '待审核',
      'approved': '已审核',
      'rejected': '已拒绝'
    }[record.status] || '未知';
    
    statusElement.innerHTML = `<span class="${statusClass}">${statusText}</span>`;
    
    // 控制审核按钮显示
    const approveBtn = document.getElementById('approve-btn');
    const rejectBtn = document.getElementById('reject-btn');
    
    if (approveBtn && rejectBtn) {
      const canApprove = record.status === 'pending' && 
                        (currentUser.role === 'admin' || currentUser.role === 'senior');
      
      approveBtn.style.display = canApprove && showApproveButtons ? 'inline-block' : 'none';
      rejectBtn.style.display = canApprove && showApproveButtons ? 'inline-block' : 'none';
      
      // 设置要审核的记录ID
      approveBtn.dataset.recordId = id;
      rejectBtn.dataset.recordId = id;
    }
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('details-modal'));
    modal.show();
  } catch (error) {
    console.error('获取销售记录详情失败:', error);
    showToast('error', '获取记录详情失败，请稍后重试');
  }
}

// 处理更新状态
async function handleUpdateStatus(status) {
  const button = status === 'approved' ? 
                document.getElementById('approve-btn') : 
                document.getElementById('reject-btn');
  
  const recordId = button.dataset.recordId;
  if (!recordId) return;
  
  try {
    const response = await apiRequest(`/sales/${recordId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        status,
        // 添加审核人信息
        approved_by_id: currentUser.id,
        approved_at: new Date().toISOString()
      })
    });
    
    if (response) {
      // 隐藏模态框
      const modal = bootstrap.Modal.getInstance(document.getElementById('details-modal'));
      modal.hide();
      
      // 显示成功消息
      const actionText = status === 'approved' ? '批准' : '拒绝';
      showToast('success', `销售记录已${actionText}`);
      
      // 重新加载列表
      loadSalesRecords();
    }
  } catch (error) {
    console.error('更新销售记录状态失败:', error);
    showToast('error', '更新状态失败，请稍后重试');
  }
}

// 显示审核模态框
function showApproveModal(orderNumber) {
  showSalesDetails(orderNumber, true);
}

// 显示删除模态框
function showDeleteModal(orderNumber) {
  // 设置要删除的记录订单号
  document.getElementById('delete-order-number').textContent = orderNumber;
  
  // 绑定删除按钮数据
  const confirmDeleteButton = document.getElementById('confirm-delete-btn');
  confirmDeleteButton.dataset.orderNumber = orderNumber;
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('delete-modal'));
  modal.show();
}

// 显示编辑模态框
function showEditModal(orderNumber) {
  showEditSalesModal(orderNumber);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initSalesPage);

// 暴露给全局的函数
window.showEditModal = showEditModal;
window.showDeleteModal = showDeleteModal;
window.showSalesDetails = showSalesDetails;
window.showApproveModal = showApproveModal; 