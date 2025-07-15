// 全局变量
let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let currentSearchQuery = '';
let currentStageFilter = '';
let currentOrderTypeFilter = '';
let currentUser = null;

// 初始化销售记录页面
async function initSalesPage() {
  // 获取当前用户
  currentUser = await getCurrentUser();
  if (!currentUser) return;
  
  // 初始化 Bootstrap tooltips
  initTooltips();
  
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
  
  // 绑定阶段筛选器更改事件
  const stageFilter = document.getElementById('stage-filter');
  if (stageFilter) {
    stageFilter.addEventListener('change', handleStageFilterChange);
  }
  
  // 绑定订单类型筛选器更改事件
  const orderTypeFilter = document.getElementById('order-type-filter');
  if (orderTypeFilter) {
    orderTypeFilter.addEventListener('change', handleOrderTypeFilterChange);
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
  
  // 绑定编辑运费保存按钮事件
  const saveShippingFeeBtn = document.getElementById('save-shipping-fee-btn');
  if (saveShippingFeeBtn) {
    saveShippingFeeBtn.addEventListener('click', saveEditedShippingFee);
  }
  
  // 绑定编辑采购保存按钮事件
  const saveProcurementBtn = document.getElementById('save-procurement-btn');
  if (saveProcurementBtn) {
    saveProcurementBtn.addEventListener('click', saveEditedProcurement);
  }
  
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
  
  // 绑定利润计算按钮事件
  const calculateProfitBtn = document.getElementById('calculate-profit-btn');
  if (calculateProfitBtn) {
    calculateProfitBtn.addEventListener('click', calculateProfit);
  }
  
  // 审核按钮已移除，现在使用表格中的阶段管理按钮
  
  // 检查URL参数，如果有id参数则打开对应记录详情
  checkUrlForRecordId();

  // 添加下拉菜单事件监听器，解决显示层级问题
  setupDropdownEventListeners();
}

// 设置下拉菜单事件监听器
function setupDropdownEventListeners() {
  // 使用事件委托监听下拉菜单的显示/隐藏
  document.addEventListener('shown.bs.dropdown', function(event) {
    // 下拉菜单显示时，设置容器overflow为visible
    const tableResponsive = document.querySelector('.table-responsive');
    const cardBody = document.querySelector('.card-body');
    
    if (tableResponsive) {
      tableResponsive.classList.add('dropdown-open');
    }
    if (cardBody) {
      cardBody.classList.add('dropdown-open');
    }
  });

  document.addEventListener('hidden.bs.dropdown', function(event) {
    // 下拉菜单隐藏时，恢复容器的overflow属性
    const tableResponsive = document.querySelector('.table-responsive');
    const cardBody = document.querySelector('.card-body');
    
    if (tableResponsive) {
      tableResponsive.classList.remove('dropdown-open');
    }
    if (cardBody) {
      cardBody.classList.remove('dropdown-open');
    }
  });
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
    
    if (currentStageFilter) {
      queryParams.append('stage', currentStageFilter);
    }
    
    if (currentOrderTypeFilter) {
      queryParams.append('order_type', currentOrderTypeFilter);
    }
    
    if (currentSearchQuery) {
      queryParams.append('search', currentSearchQuery);
    }
    
    const records = await apiRequest(`/sales?${queryParams.toString()}`, { method: 'GET' });
    if (!records) return;
    
    // 更新总条数
    totalItems = records.length; // 注意：这里应该是当前页的记录数，分页可能需要调整
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
    row.innerHTML = `<td colspan="11" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  sales.forEach(sale => {
    // 权限控制：所有用户都可以看到所有记录
    
    const row = document.createElement('tr');
    
    // 阶段显示样式和文本
    const stageClass = {
      'stage_1': 'text-info',
      'stage_2': 'text-warning', 
      'stage_3': 'text-primary',
      'stage_4': 'text-warning',
      'stage_5': 'text-success'
    }[sale.stage] || 'text-secondary';
    
    const stageText = {
      'stage_1': '初步信息补充',
      'stage_2': '待初步审核', 
      'stage_3': '运费等信息补充',
      'stage_4': '待最终审核',
      'stage_5': '审核完成'
    }[sale.stage] || '未知阶段';
    
    // 权限控制逻辑 - 根据新的审核流程
    const isCreator = sale.user_id === currentUser.id;
    const hasAdminRole = currentUser.role === 'admin' || currentUser.is_superuser;
    const hasSeniorRole = currentUser.role === 'senior';
    const hasLogisticsFunction = hasAdminRole || hasSeniorRole || 
                                 (currentUser.role === 'normal' && 
                                  (currentUser.function === 'logistics' || currentUser.function === 'sales_logistics'));
    const hasSalesFunction = hasAdminRole || hasSeniorRole || 
                            (currentUser.role === 'normal' && 
                             (currentUser.function === 'sales' || currentUser.function === 'sales_logistics'));
    
    // 各种操作权限判断
    const canView = true; // 所有用户都可以查看
    
    // 修改权限：阶段一（创建者），阶段三（后勤职能），管理员/高级用户（所有）
    const canModify = hasAdminRole || hasSeniorRole || 
                     (sale.stage === 'stage_1' && isCreator && hasSalesFunction) ||
                     (sale.stage === 'stage_3' && hasLogisticsFunction);
    
    // 删除权限：只有阶段一且是创建者本人才能删除
    const canDelete = (sale.stage === 'stage_1' && isCreator && hasSalesFunction);
    
    // 提交权限：阶段一到阶段二（创建者），阶段三到阶段四（后勤职能）
    // 注意：阶段二不能提交，只能审核通过后自动进入阶段三
    const canSubmit = (hasAdminRole || hasSeniorRole) ? 
                     (sale.stage === 'stage_1' || sale.stage === 'stage_3') : 
                     ((sale.stage === 'stage_1' && isCreator && hasSalesFunction) ||
                      (sale.stage === 'stage_3' && hasLogisticsFunction));
    
    // 审核权限：阶段二到阶段三（后勤职能），阶段四到阶段五（高级用户/管理员）
    const canApprove = (sale.stage === 'stage_2' && hasLogisticsFunction) ||
                      (sale.stage === 'stage_4' && (hasAdminRole || hasSeniorRole));
    
    // 撤回权限：复杂的撤回逻辑
    const canWithdraw = hasAdminRole || hasSeniorRole ||
                       (sale.stage === 'stage_2' && isCreator && hasSalesFunction) ||
                       (sale.stage === 'stage_3' && hasLogisticsFunction) ||
                       (sale.stage === 'stage_4' && hasLogisticsFunction) ||
                       (sale.stage === 'stage_5' && (hasAdminRole || hasSeniorRole));
    
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
    
    // 根据订单来源生成订单号前缀
    const sourcePrefix = {
      'alibaba': '阿里',
      'domestic': '国内',
      'exhibition': '展会'
    };
    const prefix = sourcePrefix[sale.order_source] || '未知';
    
    row.innerHTML = `
      <td>#${prefix}-${sale.id || 'N/A'}</td>
      <td>${sale.order_number || '-'}</td>
      <td>${sale.product_name || '-'}</td>
      <td>${sale.quantity || '0'}</td>
      <td>$${sale.unit_price ? sale.unit_price.toFixed(2) : '0.00'}</td>
      <td>$${sale.total_price ? sale.total_price.toFixed(2) : '0.00'}</td>
      <td><span class="${stageClass}">${stageText}</span></td>
      <td class="text-center">${attachmentBadge}</td>
      <td>${sale.user ? sale.user.full_name : '-'}</td>
      <td>${formatDateTime(sale.created_at)}</td>
      <td>
        <div class="d-flex align-items-center gap-1">
          <!-- 主要操作：查看（始终显示） -->
          <button class="btn btn-sm btn-info" onclick="showSalesDetails('${sale.id}')" title="查看详情">
            <i class="bi bi-eye"></i>
          </button>
          
          <!-- 主要操作：修改（根据权限显示） -->
          ${canModify ? `
            <button class="btn btn-sm btn-primary" onclick="showEditModal('${sale.id}')" title="修改记录">
              <i class="bi bi-pencil"></i>
            </button>
          ` : ''}
          
          <!-- 更多操作下拉菜单 -->
          ${(canDelete || canSubmit || canApprove || canWithdraw) ? `
            <div class="dropdown">
              <button class="btn btn-sm btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" title="更多操作">
                <i class="bi bi-three-dots"></i>
              </button>
              <ul class="dropdown-menu dropdown-menu-end">
                ${canSubmit ? `
                  <li>
                    <a class="dropdown-item" href="#" onclick="confirmAndSubmitRecord('${sale.id}', '${sale.stage}')">
                      <i class="bi bi-upload text-warning"></i> 
                      ${sale.stage === 'stage_1' ? '提交审核' : '提交最终审核'}
                    </a>
                  </li>
                ` : ''}
                
                ${canApprove ? `
                  <li>
                    <a class="dropdown-item" href="#" onclick="confirmAndApproveRecord('${sale.id}', '${sale.stage}')">
                      <i class="bi bi-check-circle text-success"></i> 
                      ${sale.stage === 'stage_2' ? '初步审核通过' : '最终审核通过'}
                    </a>
                  </li>
                ` : ''}
                
                ${canWithdraw ? `
                  <li>
                    <a class="dropdown-item" href="#" onclick="confirmAndWithdrawRecord('${sale.id}', '${sale.stage}')">
                      <i class="bi bi-arrow-counterclockwise text-secondary"></i> 撤回记录
                    </a>
                  </li>
                ` : ''}
                
                ${canDelete ? `
                  ${(canSubmit || canApprove || canWithdraw) ? '<li><hr class="dropdown-divider"></li>' : ''}
                  <li>
                    <a class="dropdown-item text-danger" href="#" onclick="confirmAndDeleteRecord('${sale.id}')">
                      <i class="bi bi-trash"></i> 删除记录
                    </a>
                  </li>
                ` : ''}
              </ul>
            </div>
          ` : ''}
          
          <!-- 状态提示 - 当用户无任何操作权限时显示 -->
          ${!canModify && !canSubmit && !canApprove && !canWithdraw && !canDelete ? `
            <span class="text-muted small">
              <i class="bi bi-lock"></i> 
              ${sale.stage === 'stage_2' ? '待审核' : 
                sale.stage === 'stage_4' ? '待审核' : 
                sale.stage === 'stage_5' ? '已完成' : '无权限'}
            </span>
          ` : ''}
        </div>
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

// 处理阶段筛选器更改
function handleStageFilterChange() {
  currentStageFilter = document.getElementById('stage-filter').value;
  currentPage = 1; // 重置为第一页
  loadSalesRecords();
}

// 处理订单类型筛选器更改
function handleOrderTypeFilterChange() {
  currentOrderTypeFilter = document.getElementById('order-type-filter').value;
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
  
  // 清空并禁用订单号字段（新增时系统还未生成）
  const orderIdInput = document.getElementById('order-id');
  if (orderIdInput) {
    orderIdInput.value = '创建后自动生成';
    orderIdInput.disabled = true;
  }
  
  // 清除订单号验证状态
  clearOrderNumberValidation();
  
  // 新增时禁用财务字段（第一阶段不能编辑财务信息）
  const exchangeRateEl = document.getElementById('exchange-rate');
  const factoryPriceEl = document.getElementById('factory-price');
  const refundAmountEl = document.getElementById('refund-amount');
  const taxRefundEl = document.getElementById('tax-refund');
  const profitEl = document.getElementById('profit');
  
  if (exchangeRateEl) exchangeRateEl.disabled = true;
  if (factoryPriceEl) factoryPriceEl.disabled = true;
  if (refundAmountEl) refundAmountEl.disabled = true;
  if (taxRefundEl) taxRefundEl.disabled = true;
  if (profitEl) profitEl.disabled = true;
  
  // 隐藏自动计算按钮（新增时不显示）
  const calculateProfitBtn = document.getElementById('calculate-profit-btn');
  if (calculateProfitBtn) {
    calculateProfitBtn.style.display = 'none';
  }
  
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
    const orderNumberEl = document.getElementById('order-number');
    const orderIdEl = document.getElementById('order-id');
    const orderTypeEl = document.getElementById('order-type');
    const orderSourceEl = document.getElementById('order-source');
    const productNameEl = document.getElementById('product-name');
    const quantityEl = document.getElementById('quantity');
    const unitPriceEl = document.getElementById('unit-price');
    const totalPriceEl = document.getElementById('total-price');
    const remarksEl = document.getElementById('remarks');
    
    // 根据阶段控制字段的可编辑性 - 按照需求文档重新设计
    const isStageOne = record.stage === 'stage_1';
    const isStageThree = record.stage === 'stage_3';
    const canModify = isStageOne || isStageThree; // 只有阶段一、三可以修改
    
    // 订单号：始终置灰不可修改（系统自动生成格式：#来源-ID）
    if (orderIdEl) {
      const sourcePrefix = {
        'alibaba': '阿里',
        'domestic': '国内',
        'exhibition': '展会'
      };
      const prefix = sourcePrefix[record.order_source] || '未知';
      orderIdEl.value = `#${prefix}-${record.id}`;
      orderIdEl.disabled = true; // 订单号始终不可修改
    }
    
    // 订单编号：阶段一可修改，其他阶段不可修改
    if (orderNumberEl) {
      orderNumberEl.value = record.order_number;
      orderNumberEl.disabled = !isStageOne; // 只有阶段一可以修改订单编号
    }
    
    // 订单类型和来源：阶段一可修改，阶段三及以上置灰
    if (orderTypeEl) {
      orderTypeEl.value = record.order_type || '';
      orderTypeEl.disabled = !isStageOne; // 只有阶段一可以修改
    }
    if (orderSourceEl) {
      orderSourceEl.value = record.order_source || '';
      orderSourceEl.disabled = !isStageOne; // 只有阶段一可以修改
    }
    
    // 产品信息：阶段一可修改，阶段三及以上置灰
    if (productNameEl) {
      productNameEl.value = record.product_name;
      productNameEl.disabled = !isStageOne; // 只有阶段一可以修改
    }
    if (quantityEl) {
      quantityEl.value = record.quantity;
      quantityEl.disabled = !isStageOne; // 只有阶段一可以修改
    }
    if (unitPriceEl) {
      unitPriceEl.value = record.unit_price;
      unitPriceEl.disabled = !isStageOne; // 只有阶段一可以修改
    }
    if (totalPriceEl) {
      totalPriceEl.value = record.total_price;
      totalPriceEl.disabled = !isStageOne; // 只有阶段一可以修改
    }
    
    // 备注：阶段一、三都可以修改
    if (remarksEl) {
      remarksEl.value = record.remarks || '';
      remarksEl.disabled = !canModify; // 阶段一、三可以修改
    }
    
    // 新增财务字段：只有第三阶段可以编辑，第一阶段置灰
    const exchangeRateEl = document.getElementById('exchange-rate');
    const factoryPriceEl = document.getElementById('factory-price');
    const refundAmountEl = document.getElementById('refund-amount');
    const taxRefundEl = document.getElementById('tax-refund');
    const profitEl = document.getElementById('profit');
    
    if (exchangeRateEl) {
      exchangeRateEl.value = record.exchange_rate || '';
      exchangeRateEl.disabled = !isStageThree; // 只有第三阶段可以编辑
    }
    if (factoryPriceEl) {
      factoryPriceEl.value = record.factory_price || '';
      factoryPriceEl.disabled = !isStageThree; // 只有第三阶段可以编辑
    }
    if (refundAmountEl) {
      refundAmountEl.value = record.refund_amount || '';
      refundAmountEl.disabled = !isStageThree; // 只有第三阶段可以编辑
    }
    if (taxRefundEl) {
      taxRefundEl.value = record.tax_refund || '';
      taxRefundEl.disabled = !isStageThree; // 只有第三阶段可以编辑
    }
    if (profitEl) {
      profitEl.value = record.profit || '';
      profitEl.disabled = !isStageThree; // 只有第三阶段可以编辑
    }
    
    // 控制自动计算按钮的显示：只在第三阶段显示
    const calculateProfitBtn = document.getElementById('calculate-profit-btn');
    if (calculateProfitBtn) {
      calculateProfitBtn.style.display = isStageThree ? 'inline-block' : 'none';
    }
    
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
    
    // 根据阶段控制运费和采购信息管理区域的显示 - 按需求只在阶段三显示
    const shippingFeesSection = document.getElementById('shipping-fees-section');
    const procurementSection = document.getElementById('procurement-section');
    
    if (shippingFeesSection && procurementSection) {
      if (isStageThree) {
        shippingFeesSection.style.display = 'block';
        procurementSection.style.display = 'block';
      } else {
        shippingFeesSection.style.display = 'none';
        procurementSection.style.display = 'none';
      }
    }
    
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
      
      // 根据阶段和用户权限检查附件编辑权限
      const hasAdminRole = currentUser.role === 'admin' || currentUser.is_superuser;
      const hasSeniorRole = currentUser.role === 'senior';
      const hasLogisticsFunction = hasAdminRole || hasSeniorRole || 
                                   (currentUser.role === 'normal' && 
                                    (currentUser.function === 'logistics' || currentUser.function === 'sales_logistics'));
      const hasSalesFunction = hasAdminRole || hasSeniorRole || 
                              (currentUser.role === 'normal' && 
                               (currentUser.function === 'sales' || currentUser.function === 'sales_logistics'));
      
      // 附件编辑权限：
      // 阶段一：创建者可以编辑销售附件
      // 阶段三：具有后勤职能的用户可以编辑后勤附件
      // 管理员/高级用户：可以在任何阶段编辑附件
      let canEditAttachments = false;
      if (hasAdminRole || hasSeniorRole) {
        canEditAttachments = true;
      } else if (record.stage === 'stage_1' && record.user_id === currentUser.id && hasSalesFunction) {
        canEditAttachments = true;
      } else if (record.stage === 'stage_3' && hasLogisticsFunction) {
        canEditAttachments = true;
      }
      
      // 根据权限显示上传区域
      if (editUploadArea) {
        editUploadArea.style.display = canEditAttachments ? 'block' : 'none';
      }
      
      console.log('编辑模式附件权限:', canEditAttachments, '用户角色:', currentUser.role, '记录阶段:', record.stage);
      console.log('编辑模式：使用已获取的记录数据，附件数量:', record.attachments ? record.attachments.length : 0);
      
      // 直接使用已获取的记录数据，避免重复请求
      if (window.attachmentsManager) {
        await window.attachmentsManager.loadAttachments(record.id, canEditAttachments, true, record); // 明确指定为编辑模式，传递记录信息
      }
      
      // 如果是阶段三，直接使用记录中的运费和采购信息
      if (isStageThree) {
        // 直接使用已获取的运费和采购信息，避免额外的API请求
        displayShippingFees(record.shipping_fees || [], record.stage);
        displayProcurement(record.procurement || [], record.stage);
        bindShippingFeesEvents(record.stage);
        bindProcurementEvents(record.stage);
      }
    }, { once: true });
  } catch (error) {
    console.error('获取销售记录详情失败:', error);
    showToast('error', '获取记录详情失败，请稍后重试');
  }
}

// 处理保存销售记录
async function handleSaveSales() {
  console.log('开始保存销售记录...');
  
  // 验证表单
  const form = document.getElementById('sales-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  console.log('表单验证通过');
  
  // 获取表单数据
  const recordId = document.getElementById('record-id').value;
  const isEdit = !!recordId;
  
  try {
    let response;
    
    if (isEdit) {
      // 首先获取当前记录信息以确定阶段
      const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
      if (!currentRecord) {
        throw new Error('无法获取记录信息');
      }
      
      const isStageThree = currentRecord.stage === 'stage_3';
      
      // 更新现有记录 - 根据阶段控制字段
      const orderNumberEl = document.getElementById('order-number');
      const orderTypeEl = document.getElementById('order-type');
      const orderSourceEl = document.getElementById('order-source');
      const productNameEl = document.getElementById('product-name');
      const quantityEl = document.getElementById('quantity');
      const unitPriceEl = document.getElementById('unit-price');
      const totalPriceEl = document.getElementById('total-price');
      const remarksEl = document.getElementById('remarks');
      
      let formData = {};
      
      if (currentRecord.stage === 'stage_1') {
        // 阶段一：可以修改所有创建时信息（包括订单编号）
        if (!orderNumberEl || !orderTypeEl || !orderSourceEl || !productNameEl || !quantityEl || !unitPriceEl || !totalPriceEl) {
          throw new Error('表单元素缺失，无法保存');
        }
        
        // 获取财务字段元素
        const exchangeRateEl = document.getElementById('exchange-rate');
        const factoryPriceEl = document.getElementById('factory-price');
        const refundAmountEl = document.getElementById('refund-amount');
        const taxRefundEl = document.getElementById('tax-refund');
        const profitEl = document.getElementById('profit');
        
        formData = {
          order_number: orderNumberEl.value.trim(),
          order_type: orderTypeEl.value,
          order_source: orderSourceEl.value,
          product_name: productNameEl.value.trim(),
          quantity: parseInt(quantityEl.value),
          unit_price: parseFloat(unitPriceEl.value),
          total_price: parseFloat(totalPriceEl.value),
          remarks: remarksEl ? remarksEl.value.trim() || null : null,
          exchange_rate: exchangeRateEl && exchangeRateEl.value ? parseFloat(exchangeRateEl.value) : null,
          factory_price: factoryPriceEl && factoryPriceEl.value ? parseFloat(factoryPriceEl.value) : null,
          refund_amount: refundAmountEl && refundAmountEl.value ? parseFloat(refundAmountEl.value) : null,
          tax_refund: taxRefundEl && taxRefundEl.value ? parseFloat(taxRefundEl.value) : null,
          profit: profitEl && profitEl.value ? parseFloat(profitEl.value) : null
        };
        console.log('阶段一编辑：保存所有基本信息');
      } else if (currentRecord.stage === 'stage_3') {
        // 阶段三：可以修改备注和财务字段
        const exchangeRateEl = document.getElementById('exchange-rate');
        const factoryPriceEl = document.getElementById('factory-price');
        const refundAmountEl = document.getElementById('refund-amount');
        const taxRefundEl = document.getElementById('tax-refund');
        const profitEl = document.getElementById('profit');
        
        formData = {
          remarks: remarksEl ? remarksEl.value.trim() || null : null,
          exchange_rate: exchangeRateEl && exchangeRateEl.value ? parseFloat(exchangeRateEl.value) : null,
          factory_price: factoryPriceEl && factoryPriceEl.value ? parseFloat(factoryPriceEl.value) : null,
          refund_amount: refundAmountEl && refundAmountEl.value ? parseFloat(refundAmountEl.value) : null,
          tax_refund: taxRefundEl && taxRefundEl.value ? parseFloat(taxRefundEl.value) : null,
          profit: profitEl && profitEl.value ? parseFloat(profitEl.value) : null
        };
        console.log('阶段三编辑：保存备注和财务字段');
      } else {
        // 其他阶段：不允许修改任何内容
        throw new Error('当前阶段不允许修改记录');
      }
      
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
      // 创建新记录 - 简化字段
      const formData = new FormData();
      
      // 添加基本字段
      const orderNumberEl = document.getElementById('order-number');
      const orderTypeEl = document.getElementById('order-type');
      const orderSourceEl = document.getElementById('order-source');
      const productNameEl = document.getElementById('product-name');
      const quantityEl = document.getElementById('quantity');
      const unitPriceEl = document.getElementById('unit-price');
      const totalPriceEl = document.getElementById('total-price');
      const remarksEl = document.getElementById('remarks');
      
      if (!orderNumberEl || !orderTypeEl || !orderSourceEl || !productNameEl || !quantityEl || !unitPriceEl || !totalPriceEl) {
        throw new Error('表单元素缺失，无法保存');
      }
      
      formData.append('order_number', orderNumberEl.value.trim());
      formData.append('order_type', orderTypeEl.value);
      formData.append('order_source', orderSourceEl.value);
      formData.append('product_name', productNameEl.value.trim());
      formData.append('quantity', parseInt(quantityEl.value));
      formData.append('unit_price', parseFloat(unitPriceEl.value));
      formData.append('total_price', parseFloat(totalPriceEl.value));
      
      const remarks = remarksEl ? remarksEl.value.trim() : '';
      if (remarks) formData.append('remarks', remarks);
      
      // 添加财务字段
      const exchangeRateEl = document.getElementById('exchange-rate');
      const factoryPriceEl = document.getElementById('factory-price');
      const refundAmountEl = document.getElementById('refund-amount');
      const taxRefundEl = document.getElementById('tax-refund');
      const profitEl = document.getElementById('profit');
      
      if (exchangeRateEl && exchangeRateEl.value) formData.append('exchange_rate', parseFloat(exchangeRateEl.value));
      if (factoryPriceEl && factoryPriceEl.value) formData.append('factory_price', parseFloat(factoryPriceEl.value));
      if (refundAmountEl && refundAmountEl.value) formData.append('refund_amount', parseFloat(refundAmountEl.value));
      if (taxRefundEl && taxRefundEl.value) formData.append('tax_refund', parseFloat(taxRefundEl.value));
      if (profitEl && profitEl.value) formData.append('profit', parseFloat(profitEl.value));
      
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



// 处理删除销售记录
async function handleDeleteSales() {
  const confirmDeleteButton = document.getElementById('confirm-delete-btn');
  const recordId = confirmDeleteButton.dataset.recordId;
  
  if (!recordId) return;
  
  try {
    const response = await apiRequest(`/sales/${recordId}`, { method: 'DELETE' });
    
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
async function showSalesDetails(id) {
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
    
    // 填充详情 - 只显示核心字段
    const setElementText = (id, text) => {
      const element = document.getElementById(id);
      if (element) element.textContent = text;
    };
    
    setElementText('detail-order-number', record.order_number);
    setElementText('detail-product-name', record.product_name);
    setElementText('detail-quantity', record.quantity);
    setElementText('detail-unit-price', parseFloat(record.unit_price).toFixed(2));
    setElementText('detail-total-price', parseFloat(record.total_price || 0).toFixed(2));
    setElementText('detail-remarks', record.remarks || '-');
    
    // 设置订单类型
    const orderTypeText = {
      'overseas': '海外订单',
      'domestic': '国内订单'
    }[record.order_type] || record.order_type || '-';
    setElementText('detail-order-type', orderTypeText);
    
    // 设置订单来源
    const orderSourceText = {
      'alibaba': '阿里',
      'domestic': '国内',
      'exhibition': '展会'
    }[record.order_source] || record.order_source || '-';
    setElementText('detail-order-source', orderSourceText);
    
    // 财务信息
    setElementText('detail-exchange-rate', record.exchange_rate || '-');
    setElementText('detail-factory-price', record.factory_price ? parseFloat(record.factory_price).toFixed(2) : '-');
    setElementText('detail-refund-amount', record.refund_amount ? parseFloat(record.refund_amount).toFixed(2) : '-');
    setElementText('detail-tax-refund', record.tax_refund ? parseFloat(record.tax_refund).toFixed(2) : '-');
    setElementText('detail-profit', record.profit ? parseFloat(record.profit).toFixed(2) : '-');
    
    setElementText('detail-creator', record.user ? record.user.full_name : '-');
    setElementText('detail-created-at', formatDateTime(record.created_at));
    setElementText('detail-created-by', record.user ? record.user.full_name : '-');
    setElementText('detail-logistics-approver', record.logistics_approved_by ? record.logistics_approved_by.full_name : '-');
    setElementText('detail-logistics-approved-at', record.logistics_approved_at ? formatDateTime(record.logistics_approved_at) : '-');
    setElementText('detail-final-approver', record.final_approved_by ? record.final_approved_by.full_name : '-');
    setElementText('detail-final-approved-at', record.final_approved_at ? formatDateTime(record.final_approved_at) : '-');
    
    // 设置阶段
    const statusElement = document.getElementById('detail-status');
    const stageClass = {
      'stage_1': 'text-info',
      'stage_2': 'text-warning', 
      'stage_3': 'text-primary',
      'stage_4': 'text-warning',
      'stage_5': 'text-success'
    }[record.stage] || 'text-secondary';
    
    const stageText = {
      'stage_1': '初步信息补充',
      'stage_2': '待初步审核', 
      'stage_3': '运费等信息补充',
      'stage_4': '待最终审核',
      'stage_5': '审核完成'
    }[record.stage] || '未知阶段';
    
    statusElement.innerHTML = `<span class="${stageClass}">${stageText}</span>`;
    
    // 审核按钮已移除，阶段操作现在通过表格中的按钮进行
    
    // 加载附件列表 - 查看模式下不允许编辑附件
    console.log('准备加载附件，attachmentsManager存在:', !!window.attachmentsManager);
    if (window.attachmentsManager) {
      await window.attachmentsManager.loadAttachments(record.id, false, false, record); // 查看模式：只读，传递记录信息
    } else {
      console.error('attachmentsManager未找到');
      showToast('error', '附件管理器未初始化');
    }
    
    // 显示运费记录（只读）
    displayDetailShippingFees(record.shipping_fees || []);
    
    // 显示采购记录（只读）
    displayDetailProcurement(record.procurement || []);
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('details-modal'));
    modal.show();
  } catch (error) {
    console.error('获取销售记录详情失败:', error);
    showToast('error', '获取记录详情失败，请稍后重试');
  }
}

// handleUpdateStatus函数已移除，现在使用新的阶段管理函数：
// handleSubmitRecord, handleApproveRecord, handleWithdrawRecord

// 显示销售记录详情（旧的审核模态框现在只是显示详情）
function showApproveModal(orderNumber) {
  showSalesDetails(orderNumber);
}

// 显示删除模态框
function showDeleteModal(recordId) {
  // 从当前记录列表中找到对应的记录来生成正确的订单号显示
  const tableRows = document.querySelectorAll('#sales-table tbody tr');
  let displayOrderNumber = `#${recordId}`;
  
  // 尝试从表格中找到对应的记录以获取正确的前缀显示
  tableRows.forEach(row => {
    const cells = row.querySelectorAll('td');
    if (cells.length > 0) {
      const orderNumberCell = cells[0];
      if (orderNumberCell.textContent.includes(`-${recordId}`)) {
        displayOrderNumber = orderNumberCell.textContent;
      }
    }
  });
  
  // 设置要删除的记录订单号
  document.getElementById('delete-order-number').textContent = displayOrderNumber;
  
  // 绑定删除按钮数据
  const confirmDeleteButton = document.getElementById('confirm-delete-btn');
  confirmDeleteButton.dataset.recordId = recordId;
  
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

// 初始化Bootstrap tooltips
function initTooltips() {
  // 初始化所有带有 data-bs-toggle="tooltip" 的元素
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// ========== 新增的阶段管理函数 ==========

// 处理提交记录到下一阶段（内部处理函数，不含确认逻辑）
async function handleSubmitRecord(recordId, currentStage) {
  const stageText = currentStage === 'stage_1' ? '初步审核' : '最终审核';

  try {
    showLoading(true);
    
    const response = await apiRequest(`/sales/${recordId}/submit`, {
      method: 'POST'
    });

    if (response) {
      showToast('success', `记录已成功提交到${stageText}阶段`);
      await loadSalesRecords(); // 重新加载列表
    }
  } catch (error) {
    console.error('提交记录失败:', error);
    showToast('error', `提交失败：${error.message || '请稍后重试'}`);
  } finally {
    showLoading(false);
  }
}

// 处理审核记录通过（内部处理函数，不含确认逻辑）
async function handleApproveRecord(recordId, currentStage) {
  const stageText = currentStage === 'stage_2' ? '初步审核' : '最终审核';

  try {
    showLoading(true);
    
    const response = await apiRequest(`/sales/${recordId}/approve`, {
      method: 'POST'
    });

    if (response) {
      showToast('success', `${stageText}已通过，记录已进入下一阶段`);
      await loadSalesRecords(); // 重新加载列表
    }
  } catch (error) {
    console.error('审核记录失败:', error);
    showToast('error', `审核失败：${error.message || '请稍后重试'}`);
  } finally {
    showLoading(false);
  }
}

// 处理撤回记录（内部处理函数，不含确认逻辑）
async function handleWithdrawRecord(recordId, currentStage) {
  let withdrawText = '';
  
  switch (currentStage) {
    case 'stage_2':
      withdrawText = '撤回到初步信息补充阶段';
      break;
    case 'stage_3':
      withdrawText = '撤回到初步信息补充阶段';
      break;
    case 'stage_4':
      withdrawText = '撤回到运费等信息补充阶段';
      break;
    case 'stage_5':
      withdrawText = '撤回到运费等信息补充阶段';
      break;
    default:
      showToast('error', '当前阶段无法撤回');
      return;
  }

  try {
    showLoading(true);
    
    const response = await apiRequest(`/sales/${recordId}/withdraw`, {
      method: 'POST'
    });

    if (response) {
      showToast('success', `记录已成功${withdrawText}`);
      await loadSalesRecords(); // 重新加载列表
    }
  } catch (error) {
    console.error('撤回记录失败:', error);
    showToast('error', `撤回失败：${error.message || '请稍后重试'}`);
  } finally {
    showLoading(false);
  }
}

// 显示/隐藏加载状态
function showLoading(show) {
  const spinner = document.querySelector('.loading-spinner');
  if (spinner) {
    spinner.style.display = show ? 'flex' : 'none';
  }
}

// 暴露新函数给全局
window.handleSubmitRecord = handleSubmitRecord;
window.handleApproveRecord = handleApproveRecord;
window.handleWithdrawRecord = handleWithdrawRecord;

// ========== 更多操作的二次确认函数 ==========

// 确认并提交记录
async function confirmAndSubmitRecord(recordId, currentStage) {
  const stageText = currentStage === 'stage_1' ? '初步审核' : '最终审核';
  
  // 显示确认对话框
  const confirmed = confirm(`确定要提交此记录到${stageText}阶段吗？\n\n提交后将无法修改记录内容，需要等待相关人员审核。`);
  
  if (confirmed) {
    await handleSubmitRecord(recordId, currentStage);
  }
}

// 确认并审核记录
async function confirmAndApproveRecord(recordId, currentStage) {
  const stageText = currentStage === 'stage_2' ? '初步审核' : '最终审核';
  
  // 显示确认对话框
  const confirmed = confirm(`确定要通过此记录的${stageText}吗？\n\n审核通过后记录将进入下一阶段，该操作不可撤销。`);
  
  if (confirmed) {
    await handleApproveRecord(recordId, currentStage);
  }
}

// 确认并撤回记录
async function confirmAndWithdrawRecord(recordId, currentStage) {
  let withdrawText = '';
  let targetStage = '';
  let confirmMessage = '';
  
  switch (currentStage) {
    case 'stage_2':
      withdrawText = '撤回到初步信息补充阶段';
      targetStage = '阶段一';
      confirmMessage = '撤回后记录将回到阶段一，销售人员可以重新修改和提交。';
      break;
    case 'stage_3':
      withdrawText = '撤回到初步信息补充阶段';
      targetStage = '阶段一';
      confirmMessage = '撤回后记录将回到阶段一，之前的审核信息将被清除。';
      break;
    case 'stage_4':
      withdrawText = '撤回到运费等信息补充阶段';
      targetStage = '阶段三';
      confirmMessage = '撤回后记录将回到阶段三，后勤人员可以重新修改和提交。';
      break;
    case 'stage_5':
      withdrawText = '撤回到运费等信息补充阶段';
      targetStage = '阶段三';
      confirmMessage = '撤回后记录将回到阶段三，最终审核信息将被清除。';
      break;
    default:
      alert('当前阶段无法撤回');
      return;
  }
  
  // 显示确认对话框
  const confirmed = confirm(`确定要${withdrawText}吗？\n\n${confirmMessage}\n\n此操作不可撤销，请谨慎操作。`);
  
  if (confirmed) {
    await handleWithdrawRecord(recordId, currentStage);
  }
}

// 确认并删除记录
async function confirmAndDeleteRecord(recordId) {
  // 显示确认对话框
  const confirmed = confirm(`确定要删除此销售记录吗？\n\n删除后将无法恢复，包括相关的附件文件也会被删除。\n\n请确认您有权限执行此操作。`);
  
  if (confirmed) {
    // 再次确认（双重确认）
    const doubleConfirmed = confirm(`请再次确认删除操作！\n\n这是最后的确认步骤，点击确定后记录将被永久删除。`);
    
    if (doubleConfirmed) {
      showDeleteModal(recordId);
    }
  }
}

// 暴露新的确认函数给全局
window.confirmAndSubmitRecord = confirmAndSubmitRecord;
window.confirmAndApproveRecord = confirmAndApproveRecord;
window.confirmAndWithdrawRecord = confirmAndWithdrawRecord;
window.confirmAndDeleteRecord = confirmAndDeleteRecord;

// ======================== 详情页面运费和采购记录显示（只读） ========================

// 显示详情页面的运费记录（只读）
function displayDetailShippingFees(shippingFees) {
  const container = document.getElementById('detail-shipping-fees-list');
  const noFeesDiv = document.getElementById('detail-no-shipping-fees');
  
  if (!container || !noFeesDiv) return;
  
  if (shippingFees.length === 0) {
    noFeesDiv.style.display = 'block';
    container.innerHTML = '';
    return;
  }
  
  noFeesDiv.style.display = 'none';
  container.innerHTML = '';
  
  shippingFees.forEach(fee => {
    const feeCard = document.createElement('div');
    feeCard.className = 'card border-success mb-2';
    feeCard.innerHTML = `
      <div class="card-body py-2">
        <div class="row align-items-center">
          <div class="col-md-2">
            <strong>${getLogisticsTypeName(fee.logistics_type)}</strong>
          </div>
          <div class="col-md-2">
            <span class="badge bg-success">¥${fee.shipping_fee.toFixed(2)}</span>
          </div>
          <div class="col-md-2">
            <small>${fee.payment_method}</small>
          </div>
          <div class="col-md-2">
            <small>${fee.logistics_company}</small>
          </div>
                     <div class="col-md-2">
             <small class="text-muted">${fee.remarks || '无备注'}</small>
           </div>
           <div class="col-md-2 text-center">
             <span class="text-muted small">只读</span>
           </div>
        </div>
      </div>
    `;
    container.appendChild(feeCard);
  });
}

// 显示详情页面的采购记录（只读）
function displayDetailProcurement(procurement) {
  const container = document.getElementById('detail-procurement-list');
  const noProcurementDiv = document.getElementById('detail-no-procurement');
  
  if (!container || !noProcurementDiv) return;
  
  if (procurement.length === 0) {
    noProcurementDiv.style.display = 'block';
    container.innerHTML = '';
    return;
  }
  
  noProcurementDiv.style.display = 'none';
  container.innerHTML = '';
  
  procurement.forEach(item => {
    const itemCard = document.createElement('div');
    itemCard.className = 'card border-info mb-2';
    itemCard.innerHTML = `
      <div class="card-body py-2">
        <div class="row">
          <div class="col-md-3">
            <div><strong>${item.procurement_item}</strong></div>
            <small class="text-muted">供应商：${item.supplier}</small>
          </div>
          <div class="col-md-2">
            <div>数量：${item.quantity}</div>
            <span class="badge bg-info">¥${item.amount.toFixed(2)}</span>
          </div>
          <div class="col-md-2">
            <div><strong>支付方式：</strong></div>
            <small class="text-muted">${item.payment_method}</small>
          </div>
          <div class="col-md-3">
            <div><strong>备注：</strong></div>
            <small class="text-muted">${item.remarks || '无备注'}</small>
          </div>
          <div class="col-md-2 text-center">
            <span class="text-muted small">只读</span>
          </div>
        </div>
      </div>
    `;
    container.appendChild(itemCard);
  });
}

// ======================== 运费信息管理 ========================

// 加载运费信息
async function loadShippingFees(salesRecordId, stage = null) {
  try {
    const shippingFees = await apiRequest(`/fees/sales-record/${salesRecordId}`, { method: 'GET' });
    displayShippingFees(shippingFees || [], stage);
  } catch (error) {
    console.error('加载运费信息失败:', error);
    displayShippingFees([], stage);
  }
}

// 显示运费信息
function displayShippingFees(shippingFees, stage = null) {
  const container = document.getElementById('shipping-fees-list');
  if (!container) return;
  
  container.innerHTML = '';
  
  if (shippingFees.length === 0) {
    container.innerHTML = '<div class="text-muted text-center py-2">暂无运费记录</div>';
    return;
  }
  
  // 判断是否可以编辑（只有阶段三可以编辑）
  const canEdit = stage === 'stage_3';
  
  shippingFees.forEach(fee => {
    const feeCard = document.createElement('div');
    feeCard.className = 'card border-success mb-2';
    feeCard.innerHTML = `
      <div class="card-body py-2">
        <div class="row align-items-center">
          <div class="col-md-2">
            <strong>${getLogisticsTypeName(fee.logistics_type)}</strong>
          </div>
          <div class="col-md-2">
            <span class="badge bg-success">¥${fee.shipping_fee.toFixed(2)}</span>
          </div>
          <div class="col-md-2">
            <small>${fee.payment_method}</small>
          </div>
          <div class="col-md-2">
            <small>${fee.logistics_company}</small>
          </div>
          <div class="col-md-2">
            <small class="text-muted">${fee.remarks || '无备注'}</small>
          </div>
          <div class="col-md-2 text-center">
            ${canEdit ? `
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="editShippingFee(${fee.id})" title="编辑">
                  <i class="bi bi-pencil"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteShippingFee(${fee.id})" title="删除">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            ` : `
              <span class="text-muted small">只读</span>
            `}
          </div>
        </div>
      </div>
    `;
    container.appendChild(feeCard);
  });
}

// 获取物流类型名称
function getLogisticsTypeName(type) {
  const typeNames = {
    'domestic_express': '国内快递',
    'domestic_logistics': '国内物流',
    'international_express': '国际快递',
    'international_logistics': '国际物流'
  };
  return typeNames[type] || type;
}

// 绑定运费相关事件
function bindShippingFeesEvents(stage = null) {
  // 判断是否可以编辑（只有阶段三可以编辑）
  const canEdit = stage === 'stage_3';
  
  // 切换添加运费表单
  const toggleBtn = document.getElementById('toggle-shipping-form');
  const formDiv = document.getElementById('shipping-fees-form');
  
  if (toggleBtn && formDiv) {
    if (canEdit) {
      toggleBtn.onclick = function() {
        const isVisible = formDiv.style.display !== 'none';
        formDiv.style.display = isVisible ? 'none' : 'block';
        const icon = toggleBtn.querySelector('i');
        if (icon) {
          icon.className = isVisible ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
        }
      };
    } else {
      // 阶段四、五时禁用添加表单
      toggleBtn.style.display = 'none';
      formDiv.style.display = 'none';
    }
  }
  
  // 添加运费记录
  const addBtn = document.getElementById('add-shipping-fee-btn');
  if (addBtn) {
    if (canEdit) {
      addBtn.onclick = addShippingFee;
    } else {
      addBtn.disabled = true;
    }
  }
}

// 添加运费记录
async function addShippingFee() {
  const recordId = document.getElementById('record-id').value;
  const logisticsType = document.getElementById('logistics-type').value;
  const feeAmount = document.getElementById('shipping-fee-amount').value;
  const paymentMethod = document.getElementById('payment-method').value;
  const logisticsCompany = document.getElementById('logistics-company').value;
  const feeRemarks = document.getElementById('shipping-fee-remarks').value;
  
  if (!feeAmount || parseFloat(feeAmount) <= 0) {
    showToast('error', '请输入有效的运费金额');
    return;
  }
  
  if (!logisticsCompany.trim()) {
    showToast('error', '请输入物流公司');
    return;
  }
  
  if (!paymentMethod.trim()) {
    showToast('error', '请输入支付方式');
    return;
  }
  
  try {
    showLoading();
    
    const data = {
      sales_record_id: parseInt(recordId),
      logistics_type: logisticsType,
      shipping_fee: parseFloat(feeAmount),
      payment_method: paymentMethod,
      logistics_company: logisticsCompany.trim(),
      remarks: feeRemarks || null
    };
    
    await apiRequest('/fees', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    
    showToast('success', '运费记录添加成功');
    
    // 清空表单
    document.getElementById('shipping-fee-amount').value = '';
    document.getElementById('payment-method').value = '';
    document.getElementById('logistics-company').value = '';
    document.getElementById('shipping-fee-remarks').value = '';
    
    // 获取当前记录的阶段信息并重新加载运费列表
    const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
    await loadShippingFees(recordId, currentRecord ? currentRecord.stage : null);
    
  } catch (error) {
    console.error('添加运费记录失败:', error);
    showToast('error', error.message || '添加运费记录失败');
  } finally {
    hideLoading();
  }
}

// 编辑运费记录
async function editShippingFee(feeId) {
  try {
    showLoading();
    
    // 获取运费记录详情
    const fee = await apiRequest(`/fees/${feeId}`, { method: 'GET' });
    if (!fee) {
      throw new Error('运费记录不存在');
    }
    
    // 填充编辑表单
    document.getElementById('edit-fee-id').value = fee.id;
    document.getElementById('edit-logistics-type').value = fee.logistics_type;
    document.getElementById('edit-shipping-fee-amount').value = fee.shipping_fee;
    document.getElementById('edit-payment-method').value = fee.payment_method;
    document.getElementById('edit-logistics-company').value = fee.logistics_company;
    document.getElementById('edit-shipping-fee-remarks').value = fee.remarks || '';
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('edit-shipping-fee-modal'));
    modal.show();
    
  } catch (error) {
    console.error('获取运费记录失败:', error);
    showToast('error', error.message || '获取运费记录失败');
  } finally {
    hideLoading();
  }
}

// 保存编辑的运费记录
async function saveEditedShippingFee() {
  const form = document.getElementById('edit-shipping-fee-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  const feeId = document.getElementById('edit-fee-id').value;
  const logisticsType = document.getElementById('edit-logistics-type').value;
  const feeAmount = document.getElementById('edit-shipping-fee-amount').value;
  const paymentMethod = document.getElementById('edit-payment-method').value;
  const logisticsCompany = document.getElementById('edit-logistics-company').value;
  const feeRemarks = document.getElementById('edit-shipping-fee-remarks').value;
  
  try {
    showLoading();
    
    const data = {
      logistics_type: logisticsType,
      shipping_fee: parseFloat(feeAmount),
      payment_method: paymentMethod.trim(),
      logistics_company: logisticsCompany.trim(),
      remarks: feeRemarks || null
    };
    
    await apiRequest(`/fees/${feeId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    
    showToast('success', '运费记录更新成功');
    
    // 隐藏模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('edit-shipping-fee-modal'));
    modal.hide();
    
    // 重新加载运费列表
    const recordId = document.getElementById('record-id').value;
    const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
    await loadShippingFees(recordId, currentRecord ? currentRecord.stage : null);
    
  } catch (error) {
    console.error('更新运费记录失败:', error);
    showToast('error', error.message || '更新运费记录失败');
  } finally {
    hideLoading();
  }
}

// 删除运费记录
async function deleteShippingFee(feeId) {
  const confirmed = confirm('确定要删除这条运费记录吗？');
  if (!confirmed) return;
  
  try {
    showLoading();
    
    await apiRequest(`/fees/${feeId}`, { method: 'DELETE' });
    showToast('success', '运费记录已删除');
    
    // 获取当前记录的阶段信息并重新加载运费列表
    const recordId = document.getElementById('record-id').value;
    const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
    await loadShippingFees(recordId, currentRecord ? currentRecord.stage : null);
    
  } catch (error) {
    console.error('删除运费记录失败:', error);
    showToast('error', error.message || '删除运费记录失败');
  } finally {
    hideLoading();
  }
}

// ======================== 采购信息管理 ========================

// 加载采购信息
async function loadProcurement(salesRecordId, stage = null) {
  try {
    const procurement = await apiRequest(`/procurement/sales-record/${salesRecordId}`, { method: 'GET' });
    displayProcurement(procurement || [], stage);
  } catch (error) {
    console.error('加载采购信息失败:', error);
    displayProcurement([], stage);
  }
}

// 显示采购信息
function displayProcurement(procurement, stage = null) {
  const container = document.getElementById('procurement-list');
  if (!container) return;
  
  container.innerHTML = '';
  
  if (procurement.length === 0) {
    container.innerHTML = '<div class="text-muted text-center py-2">暂无采购记录</div>';
    return;
  }
  
  // 判断是否可以编辑（只有阶段三可以编辑）
  const canEdit = stage === 'stage_3';
  
  procurement.forEach(item => {
    const itemCard = document.createElement('div');
    itemCard.className = 'card border-info mb-2';
    itemCard.innerHTML = `
      <div class="card-body py-2">
        <div class="row">
          <div class="col-md-3">
            <div><strong>${item.procurement_item}</strong></div>
            <small class="text-muted">供应商：${item.supplier}</small>
          </div>
          <div class="col-md-2">
            <div>数量：${item.quantity}</div>
            <span class="badge bg-info">¥${item.amount.toFixed(2)}</span>
          </div>
          <div class="col-md-2">
            <div><strong>支付方式：</strong></div>
            <small class="text-muted">${item.payment_method}</small>
          </div>
          <div class="col-md-3">
            <div><strong>备注：</strong></div>
            <small class="text-muted">${item.remarks || '无备注'}</small>
          </div>
          <div class="col-md-2 text-center">
            ${canEdit ? `
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="editProcurement(${item.id})" title="编辑">
                  <i class="bi bi-pencil"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteProcurement(${item.id})" title="删除">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            ` : `
              <span class="text-muted small">只读</span>
            `}
          </div>
        </div>
      </div>
    `;
    container.appendChild(itemCard);
  });
}

// 绑定采购相关事件
function bindProcurementEvents(stage = null) {
  // 判断是否可以编辑（只有阶段三可以编辑）
  const canEdit = stage === 'stage_3';
  
  // 切换添加采购表单
  const toggleBtn = document.getElementById('toggle-procurement-form');
  const formDiv = document.getElementById('procurement-form');
  
  if (toggleBtn && formDiv) {
    if (canEdit) {
      toggleBtn.onclick = function() {
        const isVisible = formDiv.style.display !== 'none';
        formDiv.style.display = isVisible ? 'none' : 'block';
        const icon = toggleBtn.querySelector('i');
        if (icon) {
          icon.className = isVisible ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
        }
      };
    } else {
      // 阶段四、五时禁用添加表单
      toggleBtn.style.display = 'none';
      formDiv.style.display = 'none';
    }
  }
  
  // 添加采购记录
  const addBtn = document.getElementById('add-procurement-btn');
  if (addBtn) {
    if (canEdit) {
      addBtn.onclick = addProcurement;
    } else {
      addBtn.disabled = true;
    }
  }
}

// 添加采购记录
async function addProcurement() {
  const recordId = document.getElementById('record-id').value;
  const supplier = document.getElementById('procurement-supplier').value;
  const procurementItem = document.getElementById('procurement-item').value;
  const quantity = document.getElementById('procurement-quantity').value;
  const amount = document.getElementById('procurement-amount').value;
  const paymentMethod = document.getElementById('procurement-payment').value;
  const remarks = document.getElementById('procurement-remarks').value;
  
  if (!supplier.trim()) {
    showToast('error', '请输入供应单位');
    return;
  }
  
  if (!procurementItem.trim()) {
    showToast('error', '请输入采购事项');
    return;
  }
  
  if (!quantity || parseInt(quantity) <= 0) {
    showToast('error', '请输入有效的采购数量');
    return;
  }
  
  if (!amount || parseFloat(amount) <= 0) {
    showToast('error', '请输入有效的采购金额');
    return;
  }
  
  if (!paymentMethod.trim()) {
    showToast('error', '请输入支付方式');
    return;
  }
  
  try {
    showLoading();
    
    const data = {
      sales_record_id: parseInt(recordId),
      supplier: supplier.trim(),
      procurement_item: procurementItem.trim(),
      quantity: parseInt(quantity),
      amount: parseFloat(amount),
      payment_method: paymentMethod.trim(),
      remarks: remarks || null
    };
    
    await apiRequest('/procurement', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    
    showToast('success', '采购记录添加成功');
    
    // 清空表单
    document.getElementById('procurement-supplier').value = '';
    document.getElementById('procurement-item').value = '';
    document.getElementById('procurement-quantity').value = '';
    document.getElementById('procurement-amount').value = '';
    document.getElementById('procurement-payment').value = '';
    document.getElementById('procurement-remarks').value = '';
    
    // 获取当前记录的阶段信息并重新加载采购列表
    const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
    await loadProcurement(recordId, currentRecord ? currentRecord.stage : null);
    
  } catch (error) {
    console.error('添加采购记录失败:', error);
    showToast('error', error.message || '添加采购记录失败');
  } finally {
    hideLoading();
  }
}

// 编辑采购记录
async function editProcurement(procurementId) {
  try {
    showLoading();
    
    // 获取采购记录详情
    const procurement = await apiRequest(`/procurement/${procurementId}`, { method: 'GET' });
    if (!procurement) {
      throw new Error('采购记录不存在');
    }
    
    // 填充编辑表单
    document.getElementById('edit-procurement-id').value = procurement.id;
    document.getElementById('edit-procurement-supplier').value = procurement.supplier;
    document.getElementById('edit-procurement-item').value = procurement.procurement_item;
    document.getElementById('edit-procurement-quantity').value = procurement.quantity;
    document.getElementById('edit-procurement-amount').value = procurement.amount;
    document.getElementById('edit-procurement-payment').value = procurement.payment_method;
    document.getElementById('edit-procurement-remarks').value = procurement.remarks || '';
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('edit-procurement-modal'));
    modal.show();
    
  } catch (error) {
    console.error('获取采购记录失败:', error);
    showToast('error', error.message || '获取采购记录失败');
  } finally {
    hideLoading();
  }
}

// 保存编辑的采购记录
async function saveEditedProcurement() {
  const form = document.getElementById('edit-procurement-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  const procurementId = document.getElementById('edit-procurement-id').value;
  const supplier = document.getElementById('edit-procurement-supplier').value;
  const procurementItem = document.getElementById('edit-procurement-item').value;
  const quantity = document.getElementById('edit-procurement-quantity').value;
  const amount = document.getElementById('edit-procurement-amount').value;
  const paymentMethod = document.getElementById('edit-procurement-payment').value;
  const remarks = document.getElementById('edit-procurement-remarks').value;
  
  try {
    showLoading();
    
    const data = {
      supplier: supplier.trim(),
      procurement_item: procurementItem.trim(),
      quantity: parseInt(quantity),
      amount: parseFloat(amount),
      payment_method: paymentMethod.trim(),
      remarks: remarks || null
    };
    
    await apiRequest(`/procurement/${procurementId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    
    showToast('success', '采购记录更新成功');
    
    // 隐藏模态框
    const modal = bootstrap.Modal.getInstance(document.getElementById('edit-procurement-modal'));
    modal.hide();
    
    // 重新加载采购列表
    const recordId = document.getElementById('record-id').value;
    const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
    await loadProcurement(recordId, currentRecord ? currentRecord.stage : null);
    
  } catch (error) {
    console.error('更新采购记录失败:', error);
    showToast('error', error.message || '更新采购记录失败');
  } finally {
    hideLoading();
  }
}

// 删除采购记录
async function deleteProcurement(procurementId) {
  const confirmed = confirm('确定要删除这条采购记录吗？');
  if (!confirmed) return;
  
  try {
    showLoading();
    
    await apiRequest(`/procurement/${procurementId}`, { method: 'DELETE' });
    showToast('success', '采购记录已删除');
    
    // 获取当前记录的阶段信息并重新加载采购列表
    const recordId = document.getElementById('record-id').value;
    const currentRecord = await apiRequest(`/sales/${recordId}`, { method: 'GET' });
    await loadProcurement(recordId, currentRecord ? currentRecord.stage : null);
    
  } catch (error) {
    console.error('删除采购记录失败:', error);
    showToast('error', error.message || '删除采购记录失败');
  } finally {
    hideLoading();
  }
}

// 利润自动计算函数
function calculateProfit() {
  try {
    // 获取表单元素
    const totalPriceEl = document.getElementById('total-price');
    const exchangeRateEl = document.getElementById('exchange-rate');
    const factoryPriceEl = document.getElementById('factory-price');
    const refundAmountEl = document.getElementById('refund-amount');
    const taxRefundEl = document.getElementById('tax-refund');
    const profitEl = document.getElementById('profit');
    
    if (!totalPriceEl || !exchangeRateEl || !factoryPriceEl || !profitEl) {
      showToast('error', '缺少必要的表单字段');
      return;
    }
    
    // 获取基础数据
    const totalPrice = parseFloat(totalPriceEl.value) || 0;
    const exchangeRate = parseFloat(exchangeRateEl.value) || 0;
    const factoryPrice = parseFloat(factoryPriceEl.value) || 0;
    const refundAmount = parseFloat(refundAmountEl.value) || 0;
    const taxRefund = parseFloat(taxRefundEl.value) || 0;
    
    if (totalPrice <= 0) {
      showToast('error', '请先输入有效的总价');
      return;
    }
    
    if (exchangeRate <= 0) {
      showToast('error', '请先输入有效的汇率');
      return;
    }
    
    // 获取运费总和
    let shippingTotal = 0;
    const shippingCards = document.querySelectorAll('#shipping-fees-list .badge.bg-success');
    shippingCards.forEach(badge => {
      const amount = parseFloat(badge.textContent.replace('¥', '')) || 0;
      shippingTotal += amount;
    });
    
    // 获取采购总和
    let procurementTotal = 0;
    const procurementCards = document.querySelectorAll('#procurement-list .badge.bg-info');
    procurementCards.forEach(badge => {
      const amount = parseFloat(badge.textContent.replace('¥', '')) || 0;
      procurementTotal += amount;
    });
    
    // 计算利润：总价 × 汇率 - 出厂价格 - 运费总和 - 采购总和 + 退款 + 退税
    const profit = (totalPrice * exchangeRate) - factoryPrice - shippingTotal - procurementTotal + refundAmount + taxRefund;
    
    // 设置利润值
    profitEl.value = profit.toFixed(2);
    
    // 显示计算公式
    const formulaText = `${totalPrice} × ${exchangeRate} - ${factoryPrice} - ${shippingTotal} - ${procurementTotal} + ${refundAmount} + ${taxRefund} = ${profit.toFixed(2)}`;
    
    // 查找或创建公式显示元素
    let formulaElement = document.getElementById('profit-formula');
    if (!formulaElement) {
      formulaElement = document.createElement('div');
      formulaElement.id = 'profit-formula';
      formulaElement.className = 'form-text text-info mt-1';
      profitEl.parentNode.parentNode.appendChild(formulaElement);
    }
    formulaElement.innerHTML = `<i class="bi bi-calculator"></i> 计算公式：${formulaText}`;
    
    showToast('success', `利润计算完成：¥${profit.toFixed(2)}`);
    
  } catch (error) {
    console.error('计算利润失败:', error);
    showToast('error', '计算利润失败，请检查输入数据');
  }
}

// 暴露运费和采购管理函数给全局
window.deleteShippingFee = deleteShippingFee;
window.deleteProcurement = deleteProcurement;
window.calculateProfit = calculateProfit;