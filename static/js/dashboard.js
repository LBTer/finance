// 全局变量
let currentUser = null;
let stageChart = null;
let sourceChart = null;

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
    
    // 更新图表
    updateCharts(stats);
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
    totalSalesEl.textContent = formatCurrency(stats.total_sales, '$');
  }
  
  // 更新已完成订单数（第五阶段）
  const completedOrdersEl = document.getElementById('completed-orders');
  if (completedOrdersEl && stats.stage_5_orders !== undefined) {
    completedOrdersEl.textContent = stats.stage_5_orders;
  }
  
  // 更新待后勤审核订单数（第二阶段）
  const pendingLogisticsEl = document.getElementById('pending-logistics');
  if (pendingLogisticsEl && stats.stage_2_orders !== undefined) {
    pendingLogisticsEl.textContent = stats.stage_2_orders;
  }
  
  // 更新待最终审核订单数（第四阶段）
  const pendingFinalEl = document.getElementById('pending-final');
  if (pendingFinalEl && stats.stage_4_orders !== undefined) {
    pendingFinalEl.textContent = stats.stage_4_orders;
  }
}

// 更新图表
function updateCharts(stats) {
  // 更新阶段分布图表
  updateStageChart(stats);
  
  // 更新来源分布图表
  updateSourceChart(stats);
}

// 更新阶段分布图表
function updateStageChart(stats) {
  const ctx = document.getElementById('stage-chart');
  if (!ctx) return;
  
  // 销毁现有图表
  if (stageChart) {
    stageChart.destroy();
  }
  
  const stageData = {
    labels: ['初步信息补充', '待初步审核', '运费等信息补充', '待最终审核', '审核完成'],
    datasets: [{
      data: [
        stats.stage_1_orders || 0,
        stats.stage_2_orders || 0,
        stats.stage_3_orders || 0,
        stats.stage_4_orders || 0,
        stats.stage_5_orders || 0
      ],
      backgroundColor: [
        '#4e73df',
        '#1cc88a',
        '#36b9cc',
        '#f6c23e',
        '#e74a3b'
      ],
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  };
  
  stageChart = new Chart(ctx, {
    type: 'doughnut',
    data: stageData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              size: 12
            }
          }
        }
      }
    }
  });
}

// 更新来源分布图表
function updateSourceChart(stats) {
  const ctx = document.getElementById('source-chart');
  if (!ctx) return;
  
  // 销毁现有图表
  if (sourceChart) {
    sourceChart.destroy();
  }
  
  const sourceData = {
    labels: ['阿里巴巴', '国内', '展会'],
    datasets: [{
      data: [
        stats.alibaba_orders || 0,
        stats.domestic_orders || 0,
        stats.exhibition_orders || 0
      ],
      backgroundColor: [
        '#ff6b35',
        '#4ecdc4',
        '#45b7d1'
      ],
      borderWidth: 2,
      borderColor: '#ffffff'
    }]
  };
  
  sourceChart = new Chart(ctx, {
    type: 'doughnut',
    data: sourceData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              size: 12
            }
          }
        }
      }
    }
  });
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
    row.innerHTML = `<td colspan="6" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  orders.forEach(order => {
    const row = document.createElement('tr');
    
    // 添加点击事件，可以跳转到详情页
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => showOrderDetails(order.id));
    
    // 根据订单来源生成订单号前缀
    const sourcePrefix = {
      'alibaba': '阿里',
      'domestic': '国内',
      'exhibition': '展会'
    };
    const prefix = sourcePrefix[order.order_source] || '未知';
    const displayOrderNumber = `#${prefix}-${order.id}`;
    
    // 阶段显示样式和文本
    const stageClass = {
      'stage_1': 'badge bg-info',
      'stage_2': 'badge bg-warning',
      'stage_3': 'badge bg-primary',
      'stage_4': 'badge bg-warning',
      'stage_5': 'badge bg-success'
    }[order.stage] || 'badge bg-secondary';
    
    const stageText = {
      'stage_1': '初步信息补充',
      'stage_2': '待初步审核',
      'stage_3': '运费等信息补充',
      'stage_4': '待最终审核',
      'stage_5': '审核完成'
    }[order.stage] || '未知阶段';
    
    row.innerHTML = `
      <td>${displayOrderNumber}</td>
      <td>${order.order_number}</td>
      <td>${order.product_name}</td>
      <td>${formatCurrency(order.total_price, '$')}</td>
      <td>${formatDateTime(order.created_at)}</td>
      <td><span class="${stageClass}">${stageText}</span></td>
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
function formatCurrency(amount, currency = '¥') {
  if (amount === null || amount === undefined) return `${currency}0.00`;
  
  if (currency === '$') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  } else {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(amount);
  }
}

// 格式化日期时间
function formatDateTime(dateString) {
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