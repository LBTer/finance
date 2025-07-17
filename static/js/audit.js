// 审计记录管理
let currentPage = 1;
let pageSize = 20;
let totalPages = 0;
let currentUser = null;

// 操作类型映射
const ACTION_TYPES = {
    'create': '创建',
    'update': '更新',
    'delete': '删除'
};

// 资源类型映射
const RESOURCE_TYPES = {
    'sales_record': '销售记录',
    'user': '用户',
    'attachment': '附件',
    'shipping_fees': '运费',
    'procurement': '采购'
};

// 页面初始化
async function initAuditPage() {
    try {
        // 获取当前用户信息
        currentUser = await getCurrentUser();
        if (!currentUser || currentUser.role !== 'admin') {
            showToast('error', '您没有权限访问此页面');
            window.location.href = '/dashboard';
            return;
        }
        
        // 绑定事件
        bindEvents();
        
        // 默认加载超级管理员自己的审计记录
        document.getElementById('phone-search').value = currentUser.phone;
        
        // 加载审计记录
        await loadAuditLogs();
        
    } catch (error) {
        console.error('初始化审计页面失败:', error);
        showToast('error', '页面初始化失败');
    }
}

// 绑定事件
function bindEvents() {
    // 查询表单提交
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        currentPage = 1;
        await loadAuditLogs();
    });
    
    // 重置按钮
    document.getElementById('reset-btn').addEventListener('click', () => {
        document.getElementById('search-form').reset();
        // 重置为默认显示超级管理员自己的记录
        document.getElementById('phone-search').value = currentUser.phone;
        document.getElementById('date-range').value = 'month';
        document.getElementById('custom-date-row').style.display = 'none';
        currentPage = 1;
        loadAuditLogs();
    });
    
    // 时间范围选择
    document.getElementById('date-range').addEventListener('change', (e) => {
        const customDateRow = document.getElementById('custom-date-row');
        if (e.target.value === 'custom') {
            customDateRow.style.display = 'block';
        } else {
            customDateRow.style.display = 'none';
        }
    });
}

// 加载审计记录
async function loadAuditLogs() {
    try {
        showLoading();
        
        // 构建查询参数
        const params = new URLSearchParams();
        
        // 电话号码查询
        const phone = document.getElementById('phone-search').value.trim();
        if (phone) {
            params.append('phone', phone);
        }
        
        // 操作类型
        const action = document.getElementById('action-filter').value;
        if (action) {
            params.append('action', action);
        }
        
        // 资源类型
        const resourceType = document.getElementById('resource-filter').value;
        if (resourceType) {
            params.append('resource_type', resourceType);
        }
        
        // 时间范围
        const dateRange = document.getElementById('date-range').value;
        const { startDate, endDate } = getDateRange(dateRange);
        if (startDate) {
            params.append('start_date', startDate);
        }
        if (endDate) {
            params.append('end_date', endDate);
        }
        
        // 分页参数
        params.append('page', currentPage);
        params.append('size', pageSize);
        
        // 发送请求
        const response = await apiRequest(`/audit-logs?${params.toString()}`);
        
        if (response.success) {
            renderAuditTable(response.data.items);
            renderPagination(response.data.total, response.data.page, response.data.pages);
        } else {
            showToast('error', response.message || '加载审计记录失败');
        }
        
    } catch (error) {
        console.error('加载审计记录失败:', error);
        showToast('error', '加载审计记录失败');
    } finally {
        hideLoading();
    }
}

// 通过电话号码获取用户ID
async function getUserIdByPhone(phone) {
    try {
        const response = await apiRequest(`/users?phone=${phone}&page=1&size=1`);
        if (response.success && response.data.items.length > 0) {
            return response.data.items[0].id;
        }
        return null;
    } catch (error) {
        console.error('获取用户ID失败:', error);
        return null;
    }
}

// 获取时间范围
function getDateRange(range) {
    const now = new Date();
    let startDate = null;
    let endDate = null;
    
    switch (range) {
        case 'today':
            startDate = now.toISOString().split('T')[0];
            endDate = startDate;
            break;
        case 'week':
            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            startDate = weekAgo.toISOString().split('T')[0];
            endDate = now.toISOString().split('T')[0];
            break;
        case 'month':
            const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            startDate = monthAgo.toISOString().split('T')[0];
            endDate = now.toISOString().split('T')[0];
            break;
        case 'custom':
            startDate = document.getElementById('start-date').value;
            endDate = document.getElementById('end-date').value;
            break;
    }
    
    return { startDate, endDate };
}

// 渲染审计记录表格
function renderAuditTable(auditLogs) {
    const tbody = document.getElementById('audit-table-body');
    
    if (!auditLogs || auditLogs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    <i class="bi bi-inbox"></i><br>
                    暂无审计记录
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = auditLogs.map(log => `
        <tr>
            <td>${formatDateTime(log.created_at)}</td>
            <td>
                <div class="fw-bold">${log.user_name || '系统'}</div>
                <small class="text-muted">ID: ${log.user_id || 'N/A'}</small>
            </td>
            <td>
                <span class="badge bg-${getActionBadgeClass(log.action)}">
                    ${ACTION_TYPES[log.action] || log.action}
                </span>
            </td>
            <td>
                <span class="badge bg-secondary">
                    ${RESOURCE_TYPES[log.resource_type] || log.resource_type}
                </span>
            </td>
            <td>
                <div class="text-truncate" style="max-width: 200px;" title="${log.description}">
                    ${log.description}
                </div>
            </td>
            <td>${log.ip_address || 'N/A'}</td>
            <td>
                <span class="badge bg-${log.success ? 'success' : 'danger'}">
                    ${log.success ? '成功' : '失败'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="showAuditDetail(${log.id})">
                    <i class="bi bi-eye"></i> 详情
                </button>
            </td>
        </tr>
    `).join('');
}

// 获取操作类型的徽章样式
function getActionBadgeClass(action) {
    switch (action) {
        case 'create':
            return 'success';
        case 'update':
            return 'warning';
        case 'delete':
            return 'danger';
        default:
            return 'secondary';
    }
}

// 渲染分页
function renderPagination(total, page, pages) {
    totalPages = pages;
    const container = document.getElementById('pagination-container');
    
    if (pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHtml = `
        <div class="d-flex justify-content-between align-items-center">
            <div class="text-muted">
                共 ${total} 条记录，第 ${page} 页，共 ${pages} 页
            </div>
            <ul class="pagination mb-0">
    `;
    
    // 上一页
    paginationHtml += `
        <li class="page-item ${page <= 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${page - 1})">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // 页码
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(pages, page + 2);
    
    if (startPage > 1) {
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>`;
        if (startPage > 2) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    if (endPage < pages) {
        if (endPage < pages - 1) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${pages})">${pages}</a></li>`;
    }
    
    // 下一页
    paginationHtml += `
        <li class="page-item ${page >= pages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${page + 1})">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationHtml += `
            </ul>
        </div>
    `;
    
    container.innerHTML = paginationHtml;
}

// 切换页码
async function changePage(page) {
    if (page < 1 || page > totalPages || page === currentPage) {
        return;
    }
    currentPage = page;
    await loadAuditLogs();
}

// 显示审计记录详情
async function showAuditDetail(logId) {
    try {
        showLoading();
        
        const response = await apiRequest(`/audit-logs/${logId}`);
        
        if (response.success) {
            const log = response.data;
            
            let detailsHtml = '';
            if (log.details) {
                try {
                    const details = JSON.parse(log.details);
                    detailsHtml = `
                        <div class="mt-3">
                            <h6>详细信息：</h6>
                            <pre class="bg-light p-3 rounded"><code>${JSON.stringify(details, null, 2)}</code></pre>
                        </div>
                    `;
                } catch (e) {
                    detailsHtml = `
                        <div class="mt-3">
                            <h6>详细信息：</h6>
                            <div class="bg-light p-3 rounded">${log.details}</div>
                        </div>
                    `;
                }
            }
            
            const errorInfo = log.error_message ? `
                <div class="mt-3">
                    <h6>错误信息：</h6>
                    <div class="alert alert-danger">${log.error_message}</div>
                </div>
            ` : '';
            
            document.getElementById('detail-content').innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>基本信息</h6>
                        <table class="table table-sm">
                            <tr><td><strong>时间：</strong></td><td>${formatDateTime(log.created_at)}</td></tr>
                            <tr><td><strong>用户：</strong></td><td>${log.user_name || '系统'} (ID: ${log.user_id || 'N/A'})</td></tr>
                            <tr><td><strong>操作类型：</strong></td><td><span class="badge bg-${getActionBadgeClass(log.action)}">${ACTION_TYPES[log.action] || log.action}</span></td></tr>
                            <tr><td><strong>资源类型：</strong></td><td><span class="badge bg-secondary">${RESOURCE_TYPES[log.resource_type] || log.resource_type}</span></td></tr>
                            <tr><td><strong>资源ID：</strong></td><td>${log.resource_id || 'N/A'}</td></tr>
                            <tr><td><strong>状态：</strong></td><td><span class="badge bg-${log.success ? 'success' : 'danger'}">${log.success ? '成功' : '失败'}</span></td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>请求信息</h6>
                        <table class="table table-sm">
                            <tr><td><strong>IP地址：</strong></td><td>${log.ip_address || 'N/A'}</td></tr>
                            <tr><td><strong>用户代理：</strong></td><td class="text-break">${log.user_agent || 'N/A'}</td></tr>
                        </table>
                    </div>
                </div>
                <div class="row">
                    <div class="col-12">
                        <h6>操作描述</h6>
                        <div class="bg-light p-3 rounded">${log.description}</div>
                        ${detailsHtml}
                        ${errorInfo}
                    </div>
                </div>
            `;
            
            const modal = new bootstrap.Modal(document.getElementById('detailModal'));
            modal.show();
            
        } else {
            showToast('error', response.message || '获取审计记录详情失败');
        }
        
    } catch (error) {
        console.error('获取审计记录详情失败:', error);
        showToast('error', '获取审计记录详情失败');
    } finally {
        hideLoading();
    }
}

// 格式化日期时间
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initAuditPage);