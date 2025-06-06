// 全局变量
let currentUser = null;
let userMap = {}; // 存储用户ID与角色的映射关系

// 初始化用户页面
async function initUsersPage() {
  // 获取当前用户
  currentUser = await getCurrentUser();
  if (!currentUser) return;
  
  // 检查是否有权限访问此页面
  if (currentUser.role !== 'admin' && currentUser.role !== 'senior') {
    window.location.href = '/dashboard';
    return;
  }
  
  // 加载用户列表
  loadUsers();
  
  // 绑定新增用户按钮事件
  const addButton = document.getElementById('add-user-btn');
  if (addButton) {
    addButton.addEventListener('click', showAddUserModal);
    
    // 权限控制：现在高级用户和管理员都可以创建用户
    if (currentUser.role === 'admin' || currentUser.role === 'senior') {
      addButton.classList.remove('superadmin-only');
      addButton.classList.remove('d-none');
    }
  }
  
  // 绑定保存用户按钮事件
  const saveButton = document.getElementById('save-user-btn');
  if (saveButton) {
    saveButton.addEventListener('click', handleSaveUser);
  }
  
  // 绑定重置密码按钮事件
  const resetPasswordButton = document.getElementById('reset-password-btn');
  if (resetPasswordButton) {
    resetPasswordButton.addEventListener('click', handleResetPassword);
  }
}

// 加载用户列表
async function loadUsers() {
  try {
    console.log('开始加载用户列表...');
    
    // 获取用户列表
    const users = await apiRequest('/users', { method: 'GET' });
    console.log('接收到用户数据:', users);
    
    if (!users) {
      console.log('未获取到用户数据');
      return;
    }
    
    // 构建用户映射表
    userMap = {};
    users.forEach(user => {
      userMap[user.phone] = user;
    });
    
    // 渲染用户表格
    renderUsersTable(users);
  } catch (error) {
    console.error('加载用户列表失败:', error);
    showToast('error', '加载用户列表失败，请稍后重试');
  }
}

// 渲染用户表格
function renderUsersTable(users) {
  const tableBody = document.querySelector('#users-table tbody');
  if (!tableBody) return;
  
  // 清空表格
  tableBody.innerHTML = '';
  
  if (!users || users.length === 0) {
    const row = document.createElement('tr');
    row.innerHTML = `<td colspan="7" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  users.forEach(user => {
    // 权限控制：
    // - 超级管理员可以看到所有用户
    // - 高级用户可以看到自己和普通用户
    // - 普通用户只能看到自己
    if (currentUser.role === 'normal' && user.id !== currentUser.id) {
      return;
    }
    if (currentUser.role === 'senior' && user.role === 'admin') {
      return;
    }
    
    const row = document.createElement('tr');
    
    // 状态显示样式
    const statusClass = user.is_active ? 'text-success' : 'text-danger';
    const statusText = user.is_active ? '启用' : '禁用';
    
    // 控制操作按钮显示 - 根据权限决定是否可以重置密码
    // - 超级管理员可以重置所有人的密码
    // - 高级用户可以重置自己和普通用户的密码
    // - 普通用户只能重置自己的密码
    const canReset = currentUser.role === 'admin' || 
                    (currentUser.role === 'senior' && (user.id === currentUser.id || user.role === 'normal')) ||
                    (currentUser.role === 'normal' && user.id === currentUser.id);
    
    row.innerHTML = `
      <td>${user.full_name}</td>
      <td>${user.phone}</td>
      <td>${user.email || '-'}</td>
      <td>${USER_ROLES[user.role] || '未知'}</td>
      <td><span class="${statusClass}">${statusText}</span></td>
      <td>${formatDate(user.created_at)}</td>
      <td>
        ${canReset ? `
          <button class="btn btn-sm btn-warning table-action-btn" onclick="showResetPasswordModal('${user.phone}', '${user.full_name}')">
            <i class="bi bi-key"></i> 重置密码
          </button>
        ` : ''}
      </td>
    `;
    
    tableBody.appendChild(row);
  });
}

// 显示新增用户模态框
function showAddUserModal() {
  // 重置表单
  const form = document.getElementById('user-form');
  if (form) {
    form.reset();
    form.classList.remove('was-validated');
  }
  
  // 根据当前用户角色调整可选的角色
  const roleSelect = document.getElementById('role');
  if (roleSelect) {
    // 清空现有选项
    roleSelect.innerHTML = '';
    
    // 添加普通用户选项 - 所有管理员都可以创建
    const normalOption = document.createElement('option');
    normalOption.value = 'normal';
    normalOption.textContent = '普通用户';
    roleSelect.appendChild(normalOption);
    
    // 高级用户选项 - 只有管理员可以创建
    if (currentUser.role === 'admin') {
      const seniorOption = document.createElement('option');
      seniorOption.value = 'senior';
      seniorOption.textContent = '高级用户';
      roleSelect.appendChild(seniorOption);
    }
    
    // 超级管理员选项 - 不能通过界面创建
    // 不添加超级管理员选项
  }
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('user-modal'));
  modal.show();
}

// 处理保存用户
async function handleSaveUser() {
  // 验证表单
  const form = document.getElementById('user-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  // 获取表单数据
  const formData = {
    phone: document.getElementById('phone').value.trim(),
    email: document.getElementById('email').value.trim() || null,
    full_name: document.getElementById('full-name').value.trim(),
    password: document.getElementById('password').value,
    role: document.getElementById('role').value,
    is_active: document.getElementById('is-active').checked,
    is_superuser: false  // 确保通过接口创建的用户不是超级用户
  };
  
  // 验证角色权限
  if ((currentUser.role === 'senior' && formData.role !== 'normal') ||
      formData.role === 'admin') {
    showToast('error', '您没有权限创建此角色的用户');
    return;
  }
  
  try {
    const response = await apiRequest('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    if (response) {
      // 隐藏模态框
      const modal = bootstrap.Modal.getInstance(document.getElementById('user-modal'));
      modal.hide();
      
      // 显示成功消息
      showToast('success', '用户创建成功');
      
      // 重新加载列表
      loadUsers();
    }
  } catch (error) {
    console.error('创建用户失败:', error);
    showToast('error', '创建用户失败，请稍后重试');
  }
}

// 显示重置密码模态框
function showResetPasswordModal(phone, name) {
  // 获取用户信息
  const user = userMap[phone];
  if (!user) {
    showToast('error', '找不到用户信息');
    return;
  }
  
  // 权限检查：
  // - 超级管理员可以重置所有人的密码
  // - 高级用户可以重置自己和普通用户的密码
  // - 普通用户只能重置自己的密码
  if (currentUser.role === 'normal' && user.id !== currentUser.id) {
    showToast('error', '您只能重置自己的密码');
    return;
  }
  if (currentUser.role === 'senior' && user.id !== currentUser.id && user.role !== 'normal') {
    showToast('error', '您只能重置普通用户的密码');
    return;
  }
  
  // 设置用户信息
  document.getElementById('reset-user-name').textContent = name;
  document.getElementById('reset-phone').value = phone;
  
  // 重置表单
  const form = document.getElementById('reset-password-form');
  if (form) {
    form.reset();
    form.classList.remove('was-validated');
  }
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('reset-password-modal'));
  modal.show();
}

// 处理重置密码
async function handleResetPassword() {
  // 验证表单
  const form = document.getElementById('reset-password-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  // 获取表单数据
  const phone = document.getElementById('reset-phone').value;
  const newPassword = document.getElementById('new-password').value;
  
  // 获取用户信息
  const user = userMap[phone];
  if (!user) {
    showToast('error', '找不到用户信息');
    return;
  }
  
  // 权限检查：
  // - 超级管理员可以重置所有人的密码
  // - 高级用户可以重置自己和普通用户的密码
  // - 普通用户只能重置自己的密码
  if (currentUser.role === 'normal' && user.id !== currentUser.id) {
    showToast('error', '您只能重置自己的密码');
    return;
  }
  if (currentUser.role === 'senior' && user.id !== currentUser.id && user.role !== 'normal') {
    showToast('error', '您只能重置普通用户的密码');
    return;
  }
  
  try {
    const response = await apiRequest('/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, new_password: newPassword })
    });
    
    if (response) {
      // 隐藏模态框
      const modal = bootstrap.Modal.getInstance(document.getElementById('reset-password-modal'));
      modal.hide();
      
      // 显示成功消息
      showToast('success', '密码重置成功');
    }
  } catch (error) {
    console.error('重置密码失败:', error);
    showToast('error', '重置密码失败，请稍后重试');
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initUsersPage);

// 暴露给全局的函数
window.showResetPasswordModal = showResetPasswordModal; 