// 全局变量
let currentPage = 1;
let pageSize = 10;
let totalItems = 0;
let currentLogisticsTypeFilter = '';
let currentSalesRecordFilter = '';
let currentLogisticsCompanyFilter = '';
let currentUser = null;

// 初始化运费管理页面
async function initFeesPage() {
  // 获取当前用户
  currentUser = await getCurrentUser();
  if (!currentUser) return;
  
  // 加载运费记录列表
  loadShippingFees();
  
  // 绑定统计信息按钮事件
  const statsButton = document.getElementById('stats-btn');
  if (statsButton) {
    statsButton.addEventListener('click', showStatsModal);
  }
  
  // 绑定筛选表单提交事件
  const filterForm = document.getElementById('filter-form');
  if (filterForm) {
    filterForm.addEventListener('submit', handleFilterSubmit);
  }
  
  // 绑定物流类型筛选器更改事件
  const logisticsTypeFilter = document.getElementById('logistics-type-filter');
  if (logisticsTypeFilter) {
    logisticsTypeFilter.addEventListener('change', handleLogisticsTypeFilterChange);
  }
  
  // 绑定分页事件
  const prevPageBtn = document.getElementById('prev-page');
  const nextPageBtn = document.getElementById('next-page');
  if (prevPageBtn && nextPageBtn) {
    prevPageBtn.addEventListener('click', handlePrevPage);
    nextPageBtn.addEventListener('click', handleNextPage);
  }
}

// 加载运费记录列表
async function loadShippingFees() {
  try {
    // 构建查询参数
    const queryParams = new URLSearchParams({
      skip: (currentPage - 1) * pageSize,
      limit: pageSize
    });
    
    if (currentLogisticsTypeFilter) {
      queryParams.append('logistics_type', currentLogisticsTypeFilter);
    }
    
    if (currentSalesRecordFilter) {
      queryParams.append('sales_record_id', currentSalesRecordFilter);
    }
    
    if (currentLogisticsCompanyFilter) {
      queryParams.append('logistics_company', currentLogisticsCompanyFilter);
    }
    
    const fees = await apiRequest(`/fees?${queryParams.toString()}`, { method: 'GET' });
    if (!fees) return;
    
    // 更新总条数（这里假设返回的是完整列表，实际可能需要调整）
    totalItems = fees.length;
    updatePagination();
    
    // 渲染表格
    renderFeesTable(fees);
  } catch (error) {
    console.error('加载运费记录失败:', error);
    showToast('error', '加载运费记录失败，请稍后重试');
  }
}

// 渲染运费记录表格
function renderFeesTable(fees) {
  const tableBody = document.querySelector('#fees-table tbody');
  if (!tableBody) return;
  
  // 清空表格
  tableBody.innerHTML = '';
  
  if (!fees || fees.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `<td colspan="7" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  fees.forEach(fee => {
    const row = document.createElement('tr');
    
    // 物流类型显示文本
    const logisticsTypeText = {
      'domestic_express': '国内快递',
      'international_express': '国际快递'
    }[fee.logistics_type] || fee.logistics_type;
    
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
    
    // 截断显示长文本
    const truncateText = (text, maxLength = 20) => {
      if (!text) return '-';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // 关联订单显示 - 使用#阿里-1格式
    const getOrderDisplayNumber = (record) => {
      if (!record) return `#${fee.sales_record_id}`;
      
      const sourcePrefix = {
        'alibaba': '阿里',
        'domestic': '国内',
        'exhibition': '展会'
      };
      const prefix = sourcePrefix[record.order_source] || '未知';
      const voidedBadge = record.is_voided ? '<span class="badge bg-dark text-light me-2" style="font-size: 0.7em; padding: 0.4em 0.5em;">作废</span>' : '';
      return `${voidedBadge}#${prefix}-${record.id}`;
    };
    
    const orderDisplay = fee.sales_record ? 
                     `<a href="/sales?id=${fee.sales_record.id}" class="text-primary" title="订单编号: ${fee.sales_record.order_number}">
        ${getOrderDisplayNumber(fee.sales_record)}
      </a>` : 
      `#${fee.sales_record_id}`;
  
    row.innerHTML = `
      <td>${orderDisplay}</td>
      <td>¥${fee.shipping_fee.toFixed(2)}</td>
      <td><span class="badge bg-info">${logisticsTypeText}</span></td>
      <td>${fee.payment_method}</td>
      <td title="${fee.logistics_company}">${fee.logistics_company}</td>
      <td title="${fee.remarks || ''}">${truncateText(fee.remarks)}</td>
      <td>${formatDateTime(fee.created_at)}</td>
    `;
    
    tableBody.appendChild(row);
  });
}

// 显示统计信息
async function showStatsModal() {
  // 统计信息逻辑保持不变
  try {
    showLoading();
    
    // 获取统计数据（这里可以添加统计API）
    const stats = {
      totalFees: 0,
      totalAmount: 0,
      domesticCount: 0,
      internationalCount: 0
    };
    
    // 简单示例：如果有数据，可以在这里计算统计信息
    
    // 显示统计结果
    const modal = new bootstrap.Modal(document.getElementById('stats-modal'));
    modal.show();
    
  } catch (error) {
    console.error('获取统计信息失败:', error);
    showToast('error', '获取统计信息失败，请稍后重试');
  } finally {
    hideLoading();
  }
}

// 更新分页信息
function updatePagination() {
  const paginationInfo = document.getElementById('pagination-info');
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);
  
  if (paginationInfo) {
    paginationInfo.textContent = `显示 ${startItem} 到 ${endItem} 条数据，共 ${totalItems} 条`;
  }
  
  // 更新分页按钮状态
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  
  if (prevBtn) {
    prevBtn.parentElement.classList.toggle('disabled', currentPage <= 1);
  }
  
  if (nextBtn) {
    nextBtn.parentElement.classList.toggle('disabled', currentPage * pageSize >= totalItems);
  }
}

// 处理分页
function goToPage(page) {
  if (page < 1) return;
  
  currentPage = page;
  loadShippingFees();
}

function handlePrevPage(e) {
  e.preventDefault();
  if (currentPage > 1) {
    goToPage(currentPage - 1);
  }
}

function handleNextPage(e) {
  e.preventDefault();
  if (currentPage * pageSize < totalItems) {
    goToPage(currentPage + 1);
  }
}

// 处理筛选表单提交
function handleFilterSubmit(e) {
  e.preventDefault();
  
  currentSalesRecordFilter = document.getElementById('sales-record-filter').value.trim();
  currentLogisticsCompanyFilter = document.getElementById('logistics-company-filter').value.trim();
  
  // 重置到第一页
  currentPage = 1;
  loadShippingFees();
}

// 处理物流类型筛选器改变
function handleLogisticsTypeFilterChange() {
  currentLogisticsTypeFilter = document.getElementById('logistics-type-filter').value;
  
  // 重置到第一页
  currentPage = 1;
  loadShippingFees();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initFeesPage);