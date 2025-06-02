// 全局变量
let currentUser = null;

// 初始化仪表盘页面
async function initDashboard() {
  // 获取当前用户
  currentUser = await getCurrentUser();
  if (!currentUser) return;
  
  // 加载统计数据
  loadStatistics();
  
  // 加载最近订单
  loadRecentOrders();
}

// 加载统计数据
async function loadStatistics() {
  try {
    // 获取统计数据
    const stats = await apiRequest('/stats', { method: 'GET' });
    if (!stats) return;
    
    // 更新统计卡片
    updateStatsCards(stats);
  } catch (error) {
    console.error('加载统计数据失败:', error);
    showToast('error', '加载统计数据失败，请稍后重试');
  }
}

// 更新统计卡片
function updateStatsCards(stats) {
  // 更新本月销售额
  const totalSalesEl = document.getElementById('total-sales');
  if (totalSalesEl && stats.total_sales !== undefined) {
    totalSalesEl.textContent = formatCurrency(stats.total_sales);
  }
  
  // 更新已审核订单数
  const approvedOrdersEl = document.getElementById('approved-orders');
  if (approvedOrdersEl && stats.approved_orders !== undefined) {
    approvedOrdersEl.textContent = stats.approved_orders;
  }
  
  // 更新待审核订单数
  const pendingOrdersEl = document.getElementById('pending-orders');
  if (pendingOrdersEl && stats.pending_orders !== undefined) {
    pendingOrdersEl.textContent = stats.pending_orders;
  }
  
  // 更新被拒绝订单数
  const rejectedOrdersEl = document.getElementById('rejected-orders');
  if (rejectedOrdersEl && stats.rejected_orders !== undefined) {
    rejectedOrdersEl.textContent = stats.rejected_orders;
  }
}

// 加载最近订单
async function loadRecentOrders() {
  try {
    // 获取最近10条订单
    const orders = await apiRequest('/sales?limit=10', { method: 'GET' });
    if (!orders) return;
    
    // 渲染最近订单表格
    renderRecentOrdersTable(orders);
  } catch (error) {
    console.error('加载最近订单失败:', error);
    showToast('error', '加载最近订单失败，请稍后重试');
  }
}

// 渲染最近订单表格
function renderRecentOrdersTable(orders) {
  const tableBody = document.querySelector('#recent-orders tbody');
  if (!tableBody) return;
  
  // 清空表格
  tableBody.innerHTML = '';
  
  if (!orders || orders.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `<td colspan="5" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  orders.forEach(order => {
    const row = document.createElement('tr');
    
    // 添加点击事件，可以跳转到详情页
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => showOrderDetails(order.id));
    
    // 状态显示样式
    const statusClass = order.status === 'pending' ? 'status-pending' : 
                        order.status === 'approved' ? 'status-approved' : 
                        'status-rejected';
    
    row.innerHTML = `
      <td>${order.order_number}</td>
      <td>${order.product_name}</td>
      <td>${formatCurrency(order.total_amount)}</td>
      <td>${formatDate(order.created_at)}</td>
      <td><span class="status-badge ${statusClass}">${SALES_STATUS[order.status]}</span></td>
    `;
    
    tableBody.appendChild(row);
  });
}

// 显示订单详情
function showOrderDetails(id) {
  // 重定向到销售记录页面并显示详情
  window.location.href = `/sales?id=${id}`;
}

// 格式化货币
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '¥0.00';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount);
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initDashboard);

// 暴露给全局的函数
window.showOrderDetails = showOrderDetails; 