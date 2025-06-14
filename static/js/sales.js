// 全局变量
let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let currentStatusFilter = '';
let currentSearchQuery = '';
let currentCategoryFilter = '';
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
  
  // 绑定利润计算相关字段的事件监听器
  bindProfitCalculationEvents();
  
  // 绑定订单号验证事件
  bindOrderNumberValidation();
  
  // 绑定模态框隐藏事件 - 重置附件管理器状态
  const salesModal = document.getElementById('sales-modal');
  if (salesModal) {
    salesModal.addEventListener('hidden.bs.modal', function() {
      console.log('销售记录模态框已隐藏，重置附件管理器状态');
      if (window.attachmentsManager) {
        window.attachmentsManager.clearForm();
      }
    });
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
    
    if (currentCategoryFilter) {
      queryParams.append('category', currentCategoryFilter);
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
    row.innerHTML = `<td colspan="13" class="text-center">暂无数据</td>`;
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
    // - 普通用户只能修改和删除自己的待审核记录（不能修改已审核的记录）
    const canModify = (currentUser.role === 'admin') || 
                     (currentUser.role === 'senior' && (sale.user_id === currentUser.id || sale.user.role === 'normal')) ||
                     (currentUser.role === 'normal' && sale.user_id === currentUser.id && sale.status === 'pending');
    
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
    
    // 附件数量显示
    const attachmentCount = sale.attachments ? sale.attachments.length : 0;
    const attachmentBadge = attachmentCount > 0 
      ? `<span class="badge bg-primary">${attachmentCount}</span>` 
      : '<span class="text-muted">-</span>';
    
    row.innerHTML = `
      <td>${sale.order_number}</td>
      <td>${sale.product_name}</td>
      <td>${sale.category || '-'}</td>
      <td>${sale.quantity}</td>
      <td>$${sale.unit_price.toFixed(2)}</td>
      <td>$${sale.total_price ? sale.total_price.toFixed(2) : '0.00'}</td>
      <td>${sale.exchange_rate ? sale.exchange_rate.toFixed(4) : '7.0000'}</td>
      <td>${sale.logistics_company || '-'}</td>
      <td>¥${sale.profit ? sale.profit.toFixed(2) : '0.00'}</td>
      <td><span class="${statusClass}">${statusText}</span></td>
      <td class="text-center">${attachmentBadge}</td>
      <td>${sale.user ? sale.user.full_name : '-'}</td>
      <td>${sale.approved_by ? sale.approved_by.full_name : '-'}</td>
      <td>${formatDateTime(sale.created_at)}</td>
      <td>
        <button class="btn btn-sm btn-info table-action-btn" onclick="showSalesDetails('${sale.id}')">
          <i class="bi bi-eye"></i> 查看
        </button>
        ${canModify ? `
          <button class="btn btn-sm btn-primary table-action-btn" onclick="showEditModal('${sale.id}')">
            <i class="bi bi-pencil"></i> 修改
          </button>
          <button class="btn btn-sm btn-danger table-action-btn" onclick="showDeleteModal('${sale.id}')">
            <i class="bi bi-trash"></i> 删除
          </button>
        ` : (currentUser.role === 'normal' && sale.user_id === currentUser.id && sale.status !== 'pending') ? `
          <span class="text-muted small">
            <i class="bi bi-lock"></i> 已审核，不可修改
          </span>
        ` : ''}
        ${canApprove ? `
          <button class="btn btn-sm btn-success table-action-btn" onclick="showApproveModal('${sale.id}')">
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
  currentCategoryFilter = document.getElementById('category-filter').value.trim();
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
  
  // 清理附件表单并重置状态
  if (window.attachmentsManager) {
    window.attachmentsManager.clearForm();
  }
  
  // 重新启用订单编号字段（新增时允许输入）
  const orderNumberInput = document.getElementById('order-number');
  if (orderNumberInput) {
    orderNumberInput.disabled = false;
  }
  
  // 清除订单号验证状态
  clearOrderNumberValidation();
  
  // 重新绑定利润计算事件并计算利润
  bindProfitCalculationEvents();
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('sales-modal'));
  modal.show();
  
  // 模态框显示后设置附件区域显示状态
  modal._element.addEventListener('shown.bs.modal', function() {
    // 新增模式：隐藏编辑附件区域，显示新增附件区域
    const editAttachmentsContainer = document.getElementById('edit-attachments-container');
    const editUploadArea = document.getElementById('edit-attachment-upload-area');
    const newRecordAttachments = document.getElementById('new-record-attachments');
    
    if (editAttachmentsContainer) editAttachmentsContainer.style.display = 'none';
    if (editUploadArea) editUploadArea.style.display = 'none';
    if (newRecordAttachments) newRecordAttachments.style.display = 'block';
  }, { once: true });
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
    document.getElementById('category').value = record.category || '';
    document.getElementById('quantity').value = record.quantity;
    document.getElementById('unit-price').value = record.unit_price;
    document.getElementById('total-price').value = record.total_price;
    document.getElementById('exchange-rate').value = record.exchange_rate || 7.0000;
    document.getElementById('domestic-shipping-fee').value = record.domestic_shipping_fee || 0;
    document.getElementById('overseas-shipping-fee').value = record.overseas_shipping_fee || 0;
    document.getElementById('logistics-company').value = record.logistics_company || '';
    document.getElementById('refund-amount').value = record.refund_amount || 0;
    document.getElementById('tax-refund').value = record.tax_refund || 0;
    document.getElementById('profit').value = record.profit || 0;
    document.getElementById('remarks').value = record.remarks || '';
    
    // 禁用订单编号字段（不允许修改）
    document.getElementById('order-number').disabled = true;
    
    // 只清理附件表单DOM元素，不重置状态（编辑模式下需要保持状态）
    if (window.attachmentsManager) {
      // 只清理DOM元素，不重置状态变量
      const attachmentsInput = document.getElementById('attachments');
      if (attachmentsInput) attachmentsInput.value = '';
      
      const selectedFiles = document.getElementById('selected-files');
      if (selectedFiles) selectedFiles.style.display = 'none';
      
      const fileList = document.getElementById('file-list');
      if (fileList) fileList.innerHTML = '';
      
      const newAttachments = document.getElementById('new-attachments');
      if (newAttachments) newAttachments.value = '';
      
      const editNewAttachments = document.getElementById('edit-new-attachments');
      if (editNewAttachments) editNewAttachments.value = '';
      
      // 只清空选择的文件数组，不重置其他状态
      window.attachmentsManager.selectedFiles = [];
      
      console.log('编辑模式：只清理DOM元素，保持状态变量');
    }
    
    // 重新绑定利润计算事件并计算利润
    bindProfitCalculationEvents();
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('sales-modal'));
    modal.show();
    
    // 模态框显示后加载附件列表 - 编辑模式下允许管理附件
    modal._element.addEventListener('shown.bs.modal', async function() {
      // 编辑模式：显示编辑附件区域，隐藏新增附件区域
      const editAttachmentsContainer = document.getElementById('edit-attachments-container');
      const editUploadArea = document.getElementById('edit-attachment-upload-area');
      const newRecordAttachments = document.getElementById('new-record-attachments');
      
      if (editAttachmentsContainer) editAttachmentsContainer.style.display = 'block';
      if (newRecordAttachments) newRecordAttachments.style.display = 'none';
      
      // 检查编辑权限：高级用户和超级管理员可以在任何状态下管理附件
      const canEditAttachments = (currentUser.role === 'admin' || currentUser.role === 'senior') ||
                                 (currentUser.id === record.user_id && record.status === 'pending');
      
      // 根据权限显示上传区域
      if (editUploadArea) {
        editUploadArea.style.display = canEditAttachments ? 'block' : 'none';
      }
      
      console.log('编辑模式附件权限:', canEditAttachments, '用户角色:', currentUser.role, '记录状态:', record.status);
      console.log('编辑模式：使用已获取的记录数据，附件数量:', record.attachments ? record.attachments.length : 0);
      
      // 直接使用已获取的记录数据，避免重复请求
      if (window.attachmentsManager) {
        await window.attachmentsManager.loadAttachments(record.id, canEditAttachments, true); // 明确指定为编辑模式
      }
    }, { once: true });
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
  
  // 确保利润已经计算
  calculateProfit();
  
  try {
    let response;
    
    if (isEdit) {
      // 更新现有记录
      const formData = {
        order_number: document.getElementById('order-number').value.trim(),
        product_name: document.getElementById('product-name').value.trim(),
        category: document.getElementById('category').value.trim() || null,
        quantity: parseInt(document.getElementById('quantity').value),
        unit_price: parseFloat(document.getElementById('unit-price').value),
        total_price: parseFloat(document.getElementById('total-price').value),
        exchange_rate: parseFloat(document.getElementById('exchange-rate').value) || 7.0000,
        domestic_shipping_fee: parseFloat(document.getElementById('domestic-shipping-fee').value) || 0,
        overseas_shipping_fee: parseFloat(document.getElementById('overseas-shipping-fee').value) || 0,
        logistics_company: document.getElementById('logistics-company').value.trim() || null,
        refund_amount: parseFloat(document.getElementById('refund-amount').value) || 0,
        tax_refund: parseFloat(document.getElementById('tax-refund').value) || 0,
        profit: parseFloat(document.getElementById('profit').value) || 0,
        remarks: document.getElementById('remarks').value.trim() || null
      };
      
      // 先更新销售记录
      response = await apiRequest(`/sales/${recordId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      // 如果有新选择的附件，则上传它们
      if (response && window.attachmentsManager) {
        const files = window.attachmentsManager.getFormFiles();
        if (files && files.length > 0) {
          try {
            showLoading();
            showToast('info', '正在上传附件...');
            
            const uploadFormData = new FormData();
            for (let i = 0; i < files.length; i++) {
              uploadFormData.append('files', files[i]);
            }
            
            const uploadResponse = await fetch(`/api/v1/attachments/upload/${recordId}`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${getToken()}`
              },
              body: uploadFormData
            });
            
            if (!uploadResponse.ok) {
              const error = await uploadResponse.json();
              throw new Error(error.detail || '附件上传失败');
            }
            
            const uploadResult = await uploadResponse.json();
            showToast('success', `成功上传 ${uploadResult.length} 个附件`);
            
          } catch (uploadError) {
            console.error('上传附件失败:', uploadError);
            showToast('warning', `销售记录更新成功，但附件上传失败: ${uploadError.message}`);
          } finally {
            hideLoading();
          }
        }
      }
    } else {
      // 创建新记录，支持文件上传
      const formData = new FormData();
      
      // 添加基本字段
      formData.append('order_number', document.getElementById('order-number').value.trim());
      formData.append('product_name', document.getElementById('product-name').value.trim());
      
      const category = document.getElementById('category').value.trim();
      if (category) formData.append('category', category);
      
      formData.append('quantity', parseInt(document.getElementById('quantity').value));
      formData.append('unit_price', parseFloat(document.getElementById('unit-price').value));
      formData.append('total_price', parseFloat(document.getElementById('total-price').value));
      formData.append('exchange_rate', parseFloat(document.getElementById('exchange-rate').value) || 7.0000);
      formData.append('domestic_shipping_fee', parseFloat(document.getElementById('domestic-shipping-fee').value) || 0);
      formData.append('overseas_shipping_fee', parseFloat(document.getElementById('overseas-shipping-fee').value) || 0);
      
      const logisticsCompany = document.getElementById('logistics-company').value.trim();
      if (logisticsCompany) formData.append('logistics_company', logisticsCompany);
      
      formData.append('refund_amount', parseFloat(document.getElementById('refund-amount').value) || 0);
      formData.append('tax_refund', parseFloat(document.getElementById('tax-refund').value) || 0);
      formData.append('profit', parseFloat(document.getElementById('profit').value) || 0);
      
      const remarks = document.getElementById('remarks').value.trim();
      if (remarks) formData.append('remarks', remarks);
      
      // 添加文件（如果有）
      const files = window.attachmentsManager ? window.attachmentsManager.getFormFiles() : [];
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      
      response = await fetch('/api/v1/sales', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`
        },
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '创建失败');
      }
      
      response = await response.json();
    }
    
    if (response) {
      // 清理附件表单
      if (window.attachmentsManager) {
        window.attachmentsManager.clearForm();
      }
      
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
    showToast('error', error.message || '保存记录失败，请稍后重试');
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
    document.getElementById('detail-category').textContent = record.category || '-';
    document.getElementById('detail-quantity').textContent = record.quantity;
    document.getElementById('detail-unit-price').textContent = parseFloat(record.unit_price).toFixed(2);
    document.getElementById('detail-total-price').textContent = parseFloat(record.total_price || 0).toFixed(2);
    document.getElementById('detail-exchange-rate').textContent = parseFloat(record.exchange_rate || 7.0).toFixed(4);
    document.getElementById('detail-domestic-shipping-fee').textContent = parseFloat(record.domestic_shipping_fee || 0).toFixed(2);
    document.getElementById('detail-overseas-shipping-fee').textContent = parseFloat(record.overseas_shipping_fee || 0).toFixed(2);
    document.getElementById('detail-logistics-company').textContent = record.logistics_company || '-';
    document.getElementById('detail-refund-amount').textContent = parseFloat(record.refund_amount || 0).toFixed(2);
    document.getElementById('detail-tax-refund').textContent = parseFloat(record.tax_refund || 0).toFixed(2);
    document.getElementById('detail-profit').textContent = parseFloat(record.profit || 0).toFixed(2);
    document.getElementById('detail-total-amount').textContent = parseFloat(record.total_amount || 0).toFixed(2);
    
    // 显示利润计算过程
    const totalPrice = parseFloat(record.total_price || 0);
    const exchangeRate = parseFloat(record.exchange_rate || 7.0);
    const domesticShippingFee = parseFloat(record.domestic_shipping_fee || 0);
    const overseasShippingFee = parseFloat(record.overseas_shipping_fee || 0);
    const refundAmount = parseFloat(record.refund_amount || 0);
    const taxRefund = parseFloat(record.tax_refund || 0);
    const calculatedProfit = (totalPrice * exchangeRate) - domesticShippingFee - overseasShippingFee - refundAmount + taxRefund;
    
    const detailProfitCalculation = document.getElementById('detail-profit-calculation');
    if (detailProfitCalculation) {
      detailProfitCalculation.textContent = 
        `计算过程：${totalPrice.toFixed(2)} × ${exchangeRate.toFixed(4)} - ${domesticShippingFee.toFixed(2)} - ${overseasShippingFee.toFixed(2)} - ${refundAmount.toFixed(2)} + ${taxRefund.toFixed(2)} = ¥${calculatedProfit.toFixed(2)}`;
    }
    
    document.getElementById('detail-creator').textContent = record.user ? record.user.full_name : '-';
    document.getElementById('detail-created-at').textContent = formatDateTime(record.created_at);
    document.getElementById('detail-created-by').textContent = record.user ? record.user.full_name : '-';
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
    
    // 加载附件列表 - 查看模式下不允许编辑附件
    console.log('准备加载附件，attachmentsManager存在:', !!window.attachmentsManager);
    if (window.attachmentsManager) {
      await window.attachmentsManager.loadAttachments(record.id, false, false); // 查看模式：只读
    } else {
      console.error('attachmentsManager未找到');
      showToast('error', '附件管理器未初始化');
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
        status
        // 移除手动设置的审核字段，让后端自动处理
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

// 绑定利润计算相关字段的事件监听器
function bindProfitCalculationEvents() {
  const fieldsToWatch = [
    'total-price',
    'exchange-rate', 
    'domestic-shipping-fee',
    'overseas-shipping-fee',
    'refund-amount',
    'tax-refund'
  ];
  
  fieldsToWatch.forEach(fieldId => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.addEventListener('input', calculateProfit);
      field.addEventListener('change', calculateProfit);
    }
  });
  
  // 初始计算一次
  calculateProfit();
}

// 注意：attachmentsManager现在由attachments.js提供全局实例

// 计算利润
function calculateProfit() {
  const totalPrice = parseFloat(document.getElementById('total-price')?.value) || 0;
  const exchangeRate = parseFloat(document.getElementById('exchange-rate')?.value) || 7.0;
  const domesticShippingFee = parseFloat(document.getElementById('domestic-shipping-fee')?.value) || 0;
  const overseasShippingFee = parseFloat(document.getElementById('overseas-shipping-fee')?.value) || 0;
  const refundAmount = parseFloat(document.getElementById('refund-amount')?.value) || 0;
  const taxRefund = parseFloat(document.getElementById('tax-refund')?.value) || 0;
  
  // 计算利润：总价 × 汇率 - 运费(陆内) - 运费(海运) - 退款金额 + 退税金额
  const profit = (totalPrice * exchangeRate) - domesticShippingFee - overseasShippingFee - refundAmount + taxRefund;
  
  // 更新利润字段
  const profitField = document.getElementById('profit');
  if (profitField) {
    profitField.value = profit.toFixed(2);
  }
  
  // 更新计算过程显示
  const calculationDisplay = document.getElementById('profit-calculation');
  if (calculationDisplay) {
    calculationDisplay.textContent = 
      `计算过程：${totalPrice.toFixed(2)} × ${exchangeRate.toFixed(4)} - ${domesticShippingFee.toFixed(2)} - ${overseasShippingFee.toFixed(2)} - ${refundAmount.toFixed(2)} + ${taxRefund.toFixed(2)} = ¥${profit.toFixed(2)}`;
  }
}

// 订单号验证相关变量
let orderNumberCheckTimeout = null;
let lastCheckedOrderNumber = '';

// 绑定订单号验证事件
function bindOrderNumberValidation() {
  const orderNumberInput = document.getElementById('order-number');
  if (!orderNumberInput) return;
  
  orderNumberInput.addEventListener('input', handleOrderNumberInput);
  orderNumberInput.addEventListener('blur', handleOrderNumberBlur);
}

// 处理订单号输入事件
function handleOrderNumberInput(event) {
  const orderNumber = event.target.value.trim();
  const feedback = document.getElementById('order-number-feedback');
  
  // 清除之前的定时器
  if (orderNumberCheckTimeout) {
    clearTimeout(orderNumberCheckTimeout);
  }
  
  // 如果输入为空，清除反馈
  if (!orderNumber) {
    feedback.textContent = '';
    feedback.className = 'form-text';
    return;
  }
  
  // 如果是编辑模式，不需要检查
  const recordId = document.getElementById('record-id').value;
  if (recordId) {
    feedback.textContent = '';
    feedback.className = 'form-text';
    return;
  }
  
  // 显示检查中状态
  feedback.textContent = '检查中...';
  feedback.className = 'form-text text-muted';
  
  // 设置延迟检查（防抖）
  orderNumberCheckTimeout = setTimeout(() => {
    checkOrderNumberAvailability(orderNumber);
  }, 500);
}

// 处理订单号失焦事件
function handleOrderNumberBlur(event) {
  const orderNumber = event.target.value.trim();
  
  // 如果有未完成的检查，立即执行
  if (orderNumberCheckTimeout) {
    clearTimeout(orderNumberCheckTimeout);
    if (orderNumber && orderNumber !== lastCheckedOrderNumber) {
      checkOrderNumberAvailability(orderNumber);
    }
  }
}

// 检查订单号可用性
async function checkOrderNumberAvailability(orderNumber) {
  if (!orderNumber || orderNumber === lastCheckedOrderNumber) return;
  
  const feedback = document.getElementById('order-number-feedback');
  const orderNumberInput = document.getElementById('order-number');
  
  try {
    const response = await fetch(`/api/v1/sales/check-order-number/${encodeURIComponent(orderNumber)}`, {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    if (!response.ok) {
      throw new Error('检查失败');
    }
    
    const result = await response.json();
    lastCheckedOrderNumber = orderNumber;
    
    if (result.available) {
      feedback.textContent = `✓ ${result.message}`;
      feedback.className = 'form-text text-success';
      orderNumberInput.classList.remove('is-invalid');
      orderNumberInput.classList.add('is-valid');
    } else {
      feedback.textContent = `✗ ${result.message}`;
      feedback.className = 'form-text text-danger';
      orderNumberInput.classList.remove('is-valid');
      orderNumberInput.classList.add('is-invalid');
    }
    
  } catch (error) {
    console.error('检查订单号失败:', error);
    feedback.textContent = '检查失败，请稍后重试';
    feedback.className = 'form-text text-warning';
    orderNumberInput.classList.remove('is-valid', 'is-invalid');
  }
}

// 清除订单号验证状态
function clearOrderNumberValidation() {
  const feedback = document.getElementById('order-number-feedback');
  const orderNumberInput = document.getElementById('order-number');
  
  if (feedback) {
    feedback.textContent = '';
    feedback.className = 'form-text';
  }
  
  if (orderNumberInput) {
    orderNumberInput.classList.remove('is-valid', 'is-invalid');
  }
  
  lastCheckedOrderNumber = '';
} 