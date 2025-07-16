// 全局变量
let currentUser = null;
let userMap = {}; // 存储用户ID与角色的映射关系
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;

// 职能映射
const USER_FUNCTIONS = {
  'sales': '销售',
  'logistics': '后勤', 
  'sales_logistics': '销售和后勤'
};

// 初始化用户页面
async function initUsersPage() {
  // 获取当前用户
  currentUser = await getCurrentUser();
  if (!currentUser) return;
  
  // 所有用户都可以访问用户管理页面
  // 普通用户只能看到自己的信息
  // 高级用户可以看到自己和普通用户
  // 超级管理员可以看到所有用户
  
  // 加载用户列表
  loadUsers();
  
  // 绑定新增用户按钮事件
  const addButton = document.getElementById('add-user-btn');
  if (addButton) {
    addButton.addEventListener('click', showAddUserModal);
    
    // 权限控制：只有高级用户和管理员可以创建用户
    if (currentUser.role === 'admin' || currentUser.role === 'senior') {
      addButton.classList.remove('superadmin-only');
      addButton.classList.remove('d-none');
    } else {
      addButton.style.display = 'none';
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
  
  // 绑定编辑用户信息按钮事件
  const saveEditUserButton = document.getElementById('save-edit-user-btn');
  if (saveEditUserButton) {
    saveEditUserButton.addEventListener('click', handleSaveEditUser);
  }
}

// 加载用户列表
async function loadUsers(page = 1) {
  try {
    console.log(`开始加载用户列表，第${page}页...`);
    
    // 获取用户列表（分页）
    const response = await apiRequest(`/users?page=${page}&page_size=${pageSize}`, { method: 'GET' });
    console.log('接收到用户数据:', response);
    
    if (!response) {
      console.log('未获取到用户数据');
      return;
    }
    
    // 更新分页信息
    currentPage = response.page;
    totalPages = response.total_pages;
    
    // 构建用户映射表
    userMap = {};
    response.users.forEach(user => {
      userMap[user.phone] = user;
    });
    
    // 渲染用户表格
    renderUsersTable(response.users);
    
    // 渲染分页控件
    renderPagination(response);
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
    row.innerHTML = `<td colspan="8" class="text-center">暂无数据</td>`;
    tableBody.appendChild(row);
    return;
  }
  
  // 添加每一行
  users.forEach(user => {
    // 权限控制已在后端API中处理，前端不需要额外过滤
    // 后端会根据用户角色返回相应的用户列表
    
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
    
    // 控制编辑按钮显示 - 只有超级管理员可以编辑用户信息
    const canEdit = currentUser.role === 'admin';
    
    // 职能显示逻辑
    let functionDisplay = '-';
    if (user.role === 'normal') {
      functionDisplay = USER_FUNCTIONS[user.function] || '未知';
    } else if (user.role === 'senior') {
      functionDisplay = '全部权限';
    } else if (user.role === 'admin') {
      functionDisplay = '超级管理员';
    }
    
    // 操作按钮 - 根据权限显示不同的操作
    let actionsHtml = '';
    
    // 普通用户只能重置自己的密码，不能编辑信息
    if (currentUser.role === 'normal') {
      if (user.id === currentUser.id) {
        actionsHtml = `
          <button class="btn btn-sm btn-warning table-action-btn" onclick="showResetPasswordModal('${user.phone}', '${user.full_name}')">
            <i class="bi bi-key"></i> 重置密码
          </button>
        `;
      }
    } else {
      // 高级用户和管理员可以操作相应权限范围内的用户
      actionsHtml = `
        ${canEdit ? `
          <button class="btn btn-sm btn-primary table-action-btn me-1" onclick="showEditUserModal(${user.id})">
            <i class="bi bi-pencil"></i> 编辑
          </button>
        ` : ''}
        ${canReset ? `
          <button class="btn btn-sm btn-warning table-action-btn" onclick="showResetPasswordModal('${user.phone}', '${user.full_name}')">
            <i class="bi bi-key"></i> 重置密码
          </button>
        ` : ''}
      `;
    }
    
    row.innerHTML = `
      <td>${user.full_name}</td>
      <td>${user.phone}</td>
      <td>${user.email || '-'}</td>
      <td>${USER_ROLES[user.role] || '未知'}</td>
      <td>${functionDisplay}</td>
      <td><span class="${statusClass}">${statusText}</span></td>
      <td>${formatDate(user.created_at)}</td>
      <td>
        ${actionsHtml}
      </td>
    `;
    
    tableBody.appendChild(row);
  });
}

// 渲染分页控件
function renderPagination(response) {
  const paginationContainer = document.getElementById('pagination-container');
  if (!paginationContainer) return;
  
  const { page, total_pages, total } = response;
  
  if (total_pages <= 1) {
    paginationContainer.innerHTML = '';
    return;
  }
  
  let paginationHTML = `
    <nav aria-label="用户列表分页">
      <ul class="pagination justify-content-center">
        <li class="page-item ${page === 1 ? 'disabled' : ''}">
          <a class="page-link" href="#" onclick="event.preventDefault(); if(${page} > 1) loadUsers(${page - 1})" aria-label="上一页">
            <span aria-hidden="true">&laquo;</span>
          </a>
        </li>
  `;
  
  // 计算显示的页码范围
  let startPage = Math.max(1, page - 2);
  let endPage = Math.min(total_pages, page + 2);
  
  // 如果开始页码大于1，显示第一页和省略号
  if (startPage > 1) {
    paginationHTML += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="event.preventDefault(); loadUsers(1)">1</a>
      </li>
    `;
    if (startPage > 2) {
      paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
  }
  
  // 显示页码
  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `
      <li class="page-item ${i === page ? 'active' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault(); ${i !== page ? `loadUsers(${i})` : 'return false'}">${i}</a>
      </li>
    `;
  }
  
  // 如果结束页码小于总页数，显示省略号和最后一页
  if (endPage < total_pages) {
    if (endPage < total_pages - 1) {
      paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
    paginationHTML += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="event.preventDefault(); loadUsers(${total_pages})">${total_pages}</a>
      </li>
    `;
  }
  
  paginationHTML += `
        <li class="page-item ${page === total_pages ? 'disabled' : ''}">
          <a class="page-link" href="#" onclick="event.preventDefault(); if(${page} < ${total_pages}) loadUsers(${page + 1})" aria-label="下一页">
            <span aria-hidden="true">&raquo;</span>
          </a>
        </li>
      </ul>
    </nav>
    <div class="text-center mt-2">
      <small class="text-muted">共 ${total} 条记录，第 ${page} / ${total_pages} 页</small>
    </div>
  `;
  
  paginationContainer.innerHTML = paginationHTML;
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
    
    // 添加角色选择监听器
    roleSelect.addEventListener('change', handleRoleChange);
    
    // 初始显示状态
    handleRoleChange();
  }
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('user-modal'));
  modal.show();
}

// 处理角色选择变化
function handleRoleChange() {
  const roleSelect = document.getElementById('role');
  const functionGroup = document.getElementById('function-group');
  const functionSelect = document.getElementById('function');
  
  if (!roleSelect || !functionGroup || !functionSelect) return;
  
  const selectedRole = roleSelect.value;
  
  if (selectedRole === 'normal') {
    // 普通用户需要选择职能
    functionGroup.style.display = 'block';
    functionSelect.setAttribute('required', 'required');
    // 默认选择销售
    if (!functionSelect.value) {
      functionSelect.value = 'sales';
    }
  } else {
    // 高级用户和管理员不需要选择职能
    functionGroup.style.display = 'none';
    functionSelect.removeAttribute('required');
    functionSelect.value = '';
  }
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
  
  // 如果是普通用户，添加职能字段
  if (formData.role === 'normal') {
    const functionValue = document.getElementById('function').value;
    if (!functionValue) {
      showToast('error', '请选择用户职能');
      return;
    }
    formData.function = functionValue;
  } else {
    // 高级用户和管理员默认为销售职能（虽然他们有所有权限）
    formData.function = 'sales';
  }
  
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
      
      // 重新加载当前页
      loadUsers(currentPage);
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
  document.getElementById('reset-user-phone').value = phone;
  
  // 重置表单
  const form = document.getElementById('reset-password-form');
  if (form) {
    form.reset();
    form.classList.remove('was-validated');
  }
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
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

// 显示编辑用户信息模态框
function showEditUserModal(userId) {
  // 根据用户ID查找用户
  const user = Object.values(userMap).find(u => u.id === userId);
  if (!user) {
    showToast('error', '找不到用户信息');
    return;
  }
  
  // 权限检查
  if (currentUser.role === 'normal' && user.id !== currentUser.id) {
    showToast('error', '您只能编辑自己的信息');
    return;
  }
  
  if (currentUser.role === 'senior' && user.role === 'admin') {
    showToast('error', '您没有权限编辑超级管理员');
    return;
  }
  
  // 检查是否为超级管理员
  const isSuperAdmin = user.role === 'admin';
  
  // 填充编辑表单
  document.getElementById('edit-user-id').value = user.id;
  document.getElementById('edit-full-name').value = user.full_name;
  document.getElementById('edit-email').value = user.email || '';
  document.getElementById('edit-role').value = user.role;
  document.getElementById('edit-function').value = user.function;
  document.getElementById('edit-is-active').checked = user.is_active;
  
  // 角色选择权限控制
  const roleSelect = document.getElementById('edit-role');
  if (currentUser.role === 'normal' || isSuperAdmin) {
    // 普通用户不能修改角色，超级管理员角色不可修改
    roleSelect.disabled = true;
    if (isSuperAdmin) {
      roleSelect.innerHTML = '<option value="admin">超级管理员（不可修改）</option>';
    } else {
      roleSelect.innerHTML = `<option value="${user.role}">${USER_ROLES[user.role]}（不可修改）</option>`;
    }
  } else if (currentUser.role === 'senior') {
    // 高级用户不能修改其他高级用户的角色
    if (user.role === 'senior' && user.id !== currentUser.id) {
      roleSelect.disabled = true;
      roleSelect.innerHTML = '<option value="senior">高级用户（不可修改）</option>';
    } else {
      roleSelect.disabled = false;
      roleSelect.innerHTML = `
        <option value="normal">普通用户</option>
        <option value="senior">高级用户</option>
      `;
      roleSelect.value = user.role;
    }
  } else {
    // 超级管理员可以修改所有角色（除了其他超级管理员）
    roleSelect.disabled = false;
    roleSelect.innerHTML = `
      <option value="normal">普通用户</option>
      <option value="senior">高级用户</option>
    `;
    roleSelect.value = user.role;
  }
  
  // 重置表单验证状态
  const form = document.getElementById('edit-user-form');
  if (form) {
    form.classList.remove('was-validated');
  }
  
  // 添加角色选择监听器（仅非超级管理员且可编辑时）
  if (!isSuperAdmin && !roleSelect.disabled) {
    roleSelect.addEventListener('change', handleEditRoleChange);
  }
  
  // 初始显示状态
  handleEditRoleChange();
  
  // 显示模态框
  const modal = new bootstrap.Modal(document.getElementById('edit-user-modal'));
  modal.show();
}

// 处理编辑表单中的角色选择变化
function handleEditRoleChange() {
  const roleSelect = document.getElementById('edit-role');
  const functionGroup = document.getElementById('edit-function-group');
  const functionSelect = document.getElementById('edit-function');
  
  if (!roleSelect || !functionGroup || !functionSelect) return;
  
  const selectedRole = roleSelect.value;
  
  if (selectedRole === 'normal') {
    // 普通用户需要选择职能
    functionGroup.style.display = 'block';
    functionSelect.setAttribute('required', 'required');
    // 如果当前没有选择职能，默认选择销售
    if (!functionSelect.value) {
      functionSelect.value = 'sales';
    }
  } else {
    // 高级用户不需要选择职能
    functionGroup.style.display = 'none';
    functionSelect.removeAttribute('required');
    // 高级用户默认设置为销售职能（虽然他们有所有权限）
    functionSelect.value = 'sales';
  }
}

// 处理保存编辑用户信息
async function handleSaveEditUser() {
  // 验证表单
  const form = document.getElementById('edit-user-form');
  if (!form || !form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }
  
  // 获取表单数据
  const userId = document.getElementById('edit-user-id').value;
  const roleSelect = document.getElementById('edit-role');
  
  // 查找用户信息进行权限检查
  const user = Object.values(userMap).find(u => u.id == userId);
  if (!user) {
    showToast('error', '用户不存在');
    return;
  }
  
  // 权限检查
  if (currentUser.role === 'normal' && user.id !== currentUser.id) {
    showToast('error', '您只能编辑自己的信息');
    return;
  }
  
  if (currentUser.role === 'senior' && user.role === 'admin') {
    showToast('error', '您没有权限编辑超级管理员');
    return;
  }
  
  // 检查是否为超级管理员（角色选择被禁用）
  if (roleSelect.disabled && user.role === 'admin') {
    showToast('error', '超级管理员的角色不能修改');
    return;
  }
  
  const formData = {
    full_name: document.getElementById('edit-full-name').value.trim(),
    email: document.getElementById('edit-email').value.trim() || null,
    function: document.getElementById('edit-function').value,
    is_active: document.getElementById('edit-is-active').checked
  };
  
  // 角色更新权限控制
  if (!roleSelect.disabled) {
    // 普通用户不能修改角色
    if (currentUser.role === 'normal') {
      showToast('error', '您没有权限修改角色');
      return;
    }
    
    // 高级用户不能修改其他高级用户的角色
    if (currentUser.role === 'senior' && user.role === 'senior' && user.id !== currentUser.id) {
      showToast('error', '您不能修改其他高级用户的角色');
      return;
    }
    
    formData.role = roleSelect.value;
    
    // 验证角色
    if (formData.role === 'admin') {
      showToast('error', '不能将用户角色修改为超级管理员');
      return;
    }
  }
  
  // 如果是普通用户，验证职能
  if (formData.role === 'normal' && !formData.function) {
    showToast('error', '请选择用户职能');
    return;
  }
  
  try {
    const response = await apiRequest(`/auth/users/${userId}/info`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    if (response) {
      // 隐藏模态框
      const modal = bootstrap.Modal.getInstance(document.getElementById('edit-user-modal'));
      modal.hide();
      
      // 显示成功消息
      showToast('success', '用户信息修改成功');
      
      // 重新加载当前页
      loadUsers(currentPage);
    }
  } catch (error) {
    console.error('修改用户信息失败:', error);
    showToast('error', '修改用户信息失败，请稍后重试');
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initUsersPage);

// 暴露给全局的函数
window.showResetPasswordModal = showResetPasswordModal; 
window.showEditUserModal = showEditUserModal;