// API基础路径
const API_BASE_URL = '/api/v1';

// 角色映射
const USER_ROLES = {
  'normal': '普通用户',
  'senior': '高级用户',
  'admin': '超级管理员'
};

// 销售记录状态映射
const SALES_STATUS = {
  'pending': '待审核',
  'approved': '已审核',
  'rejected': '已拒绝'
};

// 加载状态控制
function showLoading() {
  document.querySelector('.loading-spinner').classList.add('show');
}

function hideLoading() {
  document.querySelector('.loading-spinner').classList.remove('show');
}

// 获取token
function getToken() {
  return localStorage.getItem('token');
}

// 登录状态检查
function checkAuth() {
  const token = localStorage.getItem('token');
  if (!token && !window.location.href.includes('login')) {
    window.location.href = '/login';
    return false;
  }
  return true;
}

// 获取当前用户信息
async function getCurrentUser() {
  try {
    // 从JWT token中获取用户ID
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    // 解析JWT获取用户ID
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(window.atob(base64));
    
    // 使用用户ID获取用户完整信息
    if (payload.sub) {
      // 从后端API获取用户信息
      const userInfo = await apiRequest('/users/me', { method: 'GET' });
      
      if (userInfo) {
        // 更新localStorage中的用户信息
        localStorage.setItem('userRole', userInfo.role);
        localStorage.setItem('userName', userInfo.full_name);
        
        return {
          id: userInfo.id,
          role: userInfo.role,
          fullName: userInfo.full_name,
          email: userInfo.email,
          phone: userInfo.phone,
          isActive: userInfo.is_active,
          isSuperuser: userInfo.is_superuser
        };
      }
    }
    return null;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    return null;
  }
}

// API请求函数
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  };
  
  const requestOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...(options.headers || {})
    }
  };
  
  try {
    showLoading();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);
    
    // 处理401错误（未授权）
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userName');
      window.location.href = '/login';
      return null;
    }
    
    // 处理403错误（禁止访问）
    if (response.status === 403) {
      showToast('error', '无权限执行此操作');
      return null;
    }
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || '请求失败');
    }
    
    return data;
  } catch (error) {
    console.error('API请求出错:', error);
    showToast('error', error.message || '请求失败，请稍后重试');
    return null;
  } finally {
    hideLoading();
  }
}

// 提示消息
function showToast(type, message) {
  const container = document.getElementById('toast-container');
  const toastId = `toast-${Date.now()}`;
  
  const bgClass = type === 'success' ? 'bg-success' 
                : type === 'error' ? 'bg-danger'
                : type === 'warning' ? 'bg-warning'
                : 'bg-info';
  
  const icon = type === 'success' ? 'bi-check-circle-fill'
             : type === 'error' ? 'bi-exclamation-triangle-fill'
             : type === 'warning' ? 'bi-exclamation-circle-fill'
             : 'bi-info-circle-fill';
  
  const toast = document.createElement('div');
  toast.className = `toast ${bgClass} text-white`;
  toast.setAttribute('id', toastId);
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  
  toast.innerHTML = `
    <div class="toast-header ${bgClass} text-white">
      <i class="bi ${icon} me-2"></i>
      <strong class="me-auto">${type === 'success' ? '成功' : type === 'error' ? '错误' : type === 'warning' ? '警告' : '信息'}</strong>
      <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
    <div class="toast-body">
      ${message}
    </div>
  `;
  
  container.appendChild(toast);
  
  const bsToast = new bootstrap.Toast(toast, { 
    animation: true,
    autohide: true,
    delay: 4000
  });
  
  bsToast.show();
  
  // 自动删除DOM元素
  toast.addEventListener('hidden.bs.toast', () => {
    container.removeChild(toast);
  });
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-');
}

// 格式化金额
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '¥0.00';
  return '¥' + parseFloat(amount).toFixed(2);
}

// 初始化页面
async function initPage() {
  if (!checkAuth()) return;
  
  // 加载当前用户信息
  const currentUser = await getCurrentUser();
  if (currentUser) {
    document.getElementById('current-user-name').textContent = currentUser.fullName;
    document.getElementById('current-user-role').textContent = USER_ROLES[currentUser.role] || '未知角色';
    
    // 根据用户角色显示/隐藏元素
    const adminOnlyElements = document.querySelectorAll('.admin-only');
    const superadminOnlyElements = document.querySelectorAll('.superadmin-only');
    
    // 根据用户角色决定显示权限
    if (currentUser.role === 'admin') {
      // 超级管理员可以看到所有内容
      adminOnlyElements.forEach(el => el.classList.remove('d-none'));
      superadminOnlyElements.forEach(el => el.classList.remove('d-none'));
    } else if (currentUser.role === 'senior') {
      // 高级用户可以看到管理员内容，但不能看到超级管理员内容
      adminOnlyElements.forEach(el => el.classList.remove('d-none'));
      superadminOnlyElements.forEach(el => el.classList.add('d-none'));
    } else {
      // 普通用户不能看到管理内容
      adminOnlyElements.forEach(el => el.classList.add('d-none'));
      superadminOnlyElements.forEach(el => el.classList.add('d-none'));
    }
  }
  
  // 绑定退出登录事件
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userName');
      window.location.href = '/login';
    });
  }
  
  // 响应式侧边栏切换
  const sidebarToggle = document.getElementById('sidebar-toggle');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelector('.sidebar').classList.toggle('d-none');
    });
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initPage);

// 退出登录
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('userId');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userName');
  window.location.href = '/login';
} 