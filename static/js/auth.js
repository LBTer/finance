// API基础路径
const API_BASE_URL = '/api/v1';

// 加载状态控制
function showLoading() {
  document.querySelector('.loading-spinner').classList.add('show');
}

function hideLoading() {
  document.querySelector('.loading-spinner').classList.remove('show');
}

// 显示错误信息
function showError(message) {
  const errorEl = document.getElementById('login-error');
  const messageEl = document.getElementById('error-message');
  messageEl.textContent = message;
  errorEl.classList.remove('d-none');
}

// 隐藏错误信息
function hideError() {
  const errorEl = document.getElementById('login-error');
  errorEl.classList.add('d-none');
}

// 表单验证
function validateForm(form) {
  if (!form.checkValidity()) {
    form.classList.add('was-validated');
    return false;
  }
  return true;
}

// 处理登录表单提交
async function handleLogin(e) {
  e.preventDefault();
  hideError();
  
  const form = document.getElementById('login-form');
  if (!validateForm(form)) return;
  
  const phoneInput = document.getElementById('phone');
  const passwordInput = document.getElementById('password');
  
  const formData = {
    username: phoneInput.value.trim(), // 使用手机号作为用户名
    password: passwordInput.value
  };
  
  try {
    showLoading();
    
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(formData).toString()
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || '登录失败，请检查账号和密码');
    }
    
    // 保存 JWT token
    localStorage.setItem('token', data.access_token);
    
    // 解析token获取用户信息
    try {
      const base64Url = data.access_token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(window.atob(base64));
      
      // 获取用户ID并保存
      if (payload.sub) {
        localStorage.setItem('userId', payload.sub);
        
        // 由于token中无用户角色信息，这里先设置一个默认值
        // 页面初始化时会重新获取用户信息
        localStorage.setItem('userRole', payload.role || 'normal');
        localStorage.setItem('userName', payload.name || '用户');
      }
    } catch (error) {
      console.error('解析token失败:', error);
    }
    
    // 登录成功，跳转到仪表盘
    window.location.href = '/dashboard';
    
  } catch (error) {
    console.error('登录失败:', error);
    showError(error.message || '登录失败，请稍后重试');
  } finally {
    hideLoading();
  }
}

// 处理密码显示/隐藏
function togglePasswordVisibility() {
  const passwordInput = document.getElementById('password');
  const toggleButton = document.getElementById('toggle-password');
  const icon = toggleButton.querySelector('i');
  
  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    icon.classList.remove('bi-eye');
    icon.classList.add('bi-eye-slash');
  } else {
    passwordInput.type = 'password';
    icon.classList.remove('bi-eye-slash');
    icon.classList.add('bi-eye');
  }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  // 检查是否已登录
  const token = localStorage.getItem('token');
  if (token) {
    window.location.href = '/dashboard';
    return;
  }
  
  // 绑定登录表单提交事件
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  
  // 绑定密码显示/隐藏按钮事件
  const toggleButton = document.getElementById('toggle-password');
  if (toggleButton) {
    toggleButton.addEventListener('click', togglePasswordVisibility);
  }
}); 