// 附件相关功能
class AttachmentsManager {
    constructor() {
        this.currentRecordId = null;
        this.canEdit = false;
        this.selectedFiles = []; // 存储已选择的文件
        this.isEditMode = false; // 跟踪当前模式
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // 文件选择事件
        $(document).on('change', '#attachments', (e) => {
            this.handleFileSelection(e.target);
        });

        // 新附件上传事件
        $(document).on('change', '#new-attachments', (e) => {
            this.validateFiles(e.target.files);
        });

        // 上传附件按钮（详情模态框）
        $(document).on('click', '#upload-attachments-btn', () => {
            this.uploadNewAttachments();
        });

        // 上传附件按钮（编辑模态框）
        $(document).on('click', '#edit-upload-attachments-btn', () => {
            this.uploadNewAttachmentsInEditMode();
        });

        // 下载附件
        $(document).on('click', '.download-attachment', (e) => {
            const attachmentId = $(e.target).closest('.download-attachment').data('id');
            this.downloadAttachment(attachmentId);
        });

        // 删除附件
        $(document).on('click', '.delete-attachment', (e) => {
            const attachmentId = $(e.target).closest('.delete-attachment').data('id');
            const filename = $(e.target).closest('.delete-attachment').data('filename');
            this.deleteAttachment(attachmentId, filename);
        });

        // 移除已选择的文件
        $(document).on('click', '.remove-file', (e) => {
            const index = $(e.target).closest('.remove-file').data('index');
            this.removeSelectedFile(index);
        });
    }

    // 处理文件选择（累积添加）
    handleFileSelection(fileInput) {
        const newFiles = Array.from(fileInput.files);
        
        if (newFiles.length === 0) {
            return;
        }

        // 验证新文件
        const validNewFiles = this.validateFiles(newFiles);
        if (validNewFiles.length === 0) {
            // 恢复之前的文件选择
            this.updateInputFiles(fileInput);
            return;
        }

        // 添加到已选择的文件列表中
        this.selectedFiles = [...this.selectedFiles, ...validNewFiles];
        
        // 去重：基于文件名和大小
        this.selectedFiles = this.selectedFiles.filter((file, index, arr) => {
            return arr.findIndex(f => f.name === file.name && f.size === file.size) === index;
        });
        
        // 更新input的files属性
        this.updateInputFiles(fileInput);

        // 显示文件列表
        if (this.selectedFiles.length > 0) {
            this.displaySelectedFiles(this.selectedFiles);
            $('#selected-files').show();
        } else {
            $('#selected-files').hide();
        }
    }
    
    // 更新input的files属性
    updateInputFiles(fileInput) {
        const dt = new DataTransfer();
        this.selectedFiles.forEach(file => {
            dt.items.add(file);
        });
        fileInput.files = dt.files;
    }

    // 验证文件
    validateFiles(files) {
        const validFiles = [];
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain', 'text/csv'
        ];

        for (let file of files) {
            if (file.size > maxSize) {
                showToast('error', `文件 ${file.name} 过大，最大允许10MB`);
                continue;
            }

            if (!allowedTypes.includes(file.type)) {
                showToast('error', `不支持的文件类型: ${file.name}`);
                continue;
            }

            validFiles.push(file);
        }

        return validFiles;
    }

    // 显示已选择的文件
    displaySelectedFiles(files) {
        const fileList = $('#file-list');
        fileList.empty();

        files.forEach((file, index) => {
            const fileSize = this.formatFileSize(file.size);
            const fileIcon = this.getFileIcon(file.type);
            
            const fileItem = $(`
                <div class="d-flex align-items-center justify-content-between border rounded p-2 mb-2 bg-white">
                    <div class="d-flex align-items-center">
                        <i class="${fileIcon} me-2 text-primary"></i>
                        <div>
                            <div class="fw-bold">${file.name}</div>
                            <small class="text-muted">${fileSize}</small>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${index}">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            `);
            
            fileList.append(fileItem);
        });
    }

    // 移除已选择的文件
    removeSelectedFile(index) {
        const fileInput = document.getElementById('attachments');
        const indexNum = parseInt(index);
        
        // 从内部数组中移除文件
        this.selectedFiles.splice(indexNum, 1);
        
        // 更新input的files属性
        this.updateInputFiles(fileInput);
        
        if (this.selectedFiles.length === 0) {
            $('#selected-files').hide();
        } else {
            this.displaySelectedFiles(this.selectedFiles);
        }
    }

    // 加载附件列表
    async loadAttachments(recordId, canEdit = false, isEditMode = false) {
        console.log('loadAttachments - recordId:', recordId, 'canEdit:', canEdit, 'isEditMode:', isEditMode);
        
        this.currentRecordId = recordId;
        this.canEdit = canEdit;
        this.isEditMode = isEditMode; // 保存当前模式

        try {
            const token = getToken();
            console.log('使用token:', token ? '已获取' : '未获取');
            
            const response = await fetch(`/api/v1/attachments/${recordId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            console.log('API响应状态:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API错误响应:', errorText);
                throw new Error('获取附件列表失败');
            }

            const attachments = await response.json();
            console.log('获取到的附件数据:', attachments);
            this.displayAttachments(attachments, isEditMode);
            
            // 根据权限显示上传区域 - 在displayAttachments中处理

        } catch (error) {
            console.error('加载附件失败:', error);
            showToast('error', '加载附件列表失败');
        }
    }

    // 显示附件列表
    displayAttachments(attachments, isEditMode = false) {
        console.log('displayAttachments - 附件数量:', attachments.length, 'isEditMode:', isEditMode);
        
        let container, noAttachments, uploadArea;
        
        if (isEditMode) {
            // 编辑模式：使用编辑模态框的元素
            container = document.getElementById('edit-attachments-list');
            noAttachments = document.getElementById('edit-no-attachments');
            uploadArea = document.getElementById('edit-attachment-upload-area');
        } else {
            // 查看模式：使用详情模态框的元素
            container = document.getElementById('attachments-list');
            noAttachments = document.getElementById('no-attachments');
            uploadArea = document.getElementById('attachment-upload-area');
        }
        
        if (!container || !noAttachments) {
            console.error('附件显示容器元素未找到');
            return;
        }
        
        // 根据权限显示上传区域
        if (uploadArea) {
            if (this.canEdit) {
                uploadArea.style.display = 'block';
            } else {
                uploadArea.style.display = 'none';
            }
        }
        
        // 在编辑模式下，控制新增记录附件区域的显示
        if (isEditMode) {
            const newRecordAttachments = document.getElementById('new-record-attachments');
            if (newRecordAttachments) {
                newRecordAttachments.style.display = 'none';
            }
        } else {
            const newRecordAttachments = document.getElementById('new-record-attachments');
            if (newRecordAttachments) {
                newRecordAttachments.style.display = 'block';
            }
        }

        if (attachments.length === 0) {
            container.style.display = 'none';
            noAttachments.style.display = 'block';
            return;
        }

        noAttachments.style.display = 'none';
        container.style.display = 'block';
        container.innerHTML = '';

        attachments.forEach(attachment => {
            const fileSize = this.formatFileSize(attachment.file_size);
            const fileIcon = this.getFileIcon(attachment.content_type);
            const createdAt = new Date(attachment.created_at).toLocaleString('zh-CN');
            
            const attachmentCard = document.createElement('div');
            // 使用全宽长条形卡片
            attachmentCard.className = 'col-12 mb-2';
            attachmentCard.innerHTML = `
                <div class="card border-secondary" style="height: 70px;">
                    <div class="card-body d-flex align-items-center p-3">
                        <div class="d-flex align-items-center flex-grow-1">
                            <i class="${fileIcon} me-3 text-primary fs-4"></i>
                            <div class="flex-grow-1">
                                <div class="fw-bold text-truncate mb-1" title="${attachment.original_filename}">
                                    ${attachment.original_filename}
                                </div>
                                <div class="d-flex gap-3">
                                    <small class="text-muted">${fileSize}</small>
                                    <small class="text-muted">${createdAt}</small>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex gap-2 ms-3">
                            <button type="button" class="btn btn-sm btn-outline-primary download-attachment" 
                                    data-id="${attachment.id}" title="下载">
                                <i class="bi bi-download"></i> 下载
                            </button>
                            ${this.canEdit ? `
                            <button type="button" class="btn btn-sm btn-outline-danger delete-attachment" 
                                    data-id="${attachment.id}" data-filename="${attachment.original_filename}" title="删除">
                                <i class="bi bi-trash"></i> 删除
                            </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(attachmentCard);
        });
    }

    // 上传新附件（详情模态框）
    async uploadNewAttachments() {
        const fileInput = document.getElementById('new-attachments');
        const files = fileInput.files;
        
        if (files.length === 0) {
            showToast('warning', '请选择要上传的文件');
            return;
        }

        if (!this.currentRecordId) {
            showToast('error', '无法确定销售记录ID');
            return;
        }

        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });

        try {
            showLoading();
            
            const response = await fetch(`/api/v1/attachments/upload/${this.currentRecordId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '上传失败');
            }

            const result = await response.json();
            showToast('success', `成功上传 ${result.length} 个文件`);
            
            // 清空文件选择
            fileInput.value = '';
            
            // 重新加载附件列表
            await this.loadAttachments(this.currentRecordId, this.canEdit, false); // 查看模式上传

        } catch (error) {
            console.error('上传附件失败:', error);
            showToast('error', error.message || '上传附件失败');
        } finally {
            hideLoading();
        }
    }

    // 上传新附件（编辑模态框）
    async uploadNewAttachmentsInEditMode() {
        const fileInput = document.getElementById('edit-new-attachments');
        const files = fileInput.files;
        
        if (files.length === 0) {
            showToast('warning', '请选择要上传的文件');
            return;
        }

        if (!this.currentRecordId) {
            showToast('error', '无法确定销售记录ID');
            return;
        }

        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });

        try {
            showLoading();
            
            const response = await fetch(`/api/v1/attachments/upload/${this.currentRecordId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '上传失败');
            }

            const result = await response.json();
            showToast('success', `成功上传 ${result.length} 个文件`);
            
            // 清空文件选择
            fileInput.value = '';
            
            // 重新加载附件列表
            await this.loadAttachments(this.currentRecordId, this.canEdit, true); // 编辑模式上传
            
            // 更新主列表中的附件数量显示
            this.updateMainListAttachmentCount(this.currentRecordId);

        } catch (error) {
            console.error('上传附件失败:', error);
            showToast('error', error.message || '上传附件失败');
        } finally {
            hideLoading();
        }
    }

    // 下载附件
    async downloadAttachment(attachmentId) {
        try {
            showLoading();
            
            const response = await fetch(`/api/v1/attachments/download/${attachmentId}`, {
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('下载失败');
            }

            // 获取文件名
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'download';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }

            // 下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showToast('success', '文件下载开始');

        } catch (error) {
            console.error('下载附件失败:', error);
            showToast('error', '下载附件失败');
        } finally {
            hideLoading();
        }
    }

    // 删除附件
    async deleteAttachment(attachmentId, filename) {
        if (!confirm(`确定要删除文件 "${filename}" 吗？此操作不可撤销。`)) {
            return;
        }

        try {
            showLoading();
            
            const response = await fetch(`/api/v1/attachments/${attachmentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '删除失败');
            }

            showToast('success', `文件 "${filename}" 已删除`);
            
            // 重新加载附件列表
            await this.loadAttachments(this.currentRecordId, this.canEdit, this.isEditMode); // 使用保存的模式
            
            // 更新主列表中的附件数量显示
            this.updateMainListAttachmentCount(this.currentRecordId);

        } catch (error) {
            console.error('删除附件失败:', error);
            showToast('error', error.message || '删除附件失败');
        } finally {
            hideLoading();
        }
    }

    // 获取文件图标
    getFileIcon(contentType) {
        if (contentType.startsWith('image/')) {
            return 'bi bi-file-earmark-image';
        } else if (contentType === 'application/pdf') {
            return 'bi bi-file-earmark-pdf';
        } else if (contentType.includes('word')) {
            return 'bi bi-file-earmark-word';
        } else if (contentType.includes('excel') || contentType.includes('sheet')) {
            return 'bi bi-file-earmark-excel';
        } else if (contentType.startsWith('text/')) {
            return 'bi bi-file-earmark-text';
        } else {
            return 'bi bi-file-earmark';
        }
    }

    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 清理表单
    clearForm() {
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
        
        // 重置所有状态变量
        this.selectedFiles = []; // 清空内部文件数组
        this.currentRecordId = null; // 重置记录ID
        this.canEdit = false; // 重置编辑权限
        this.isEditMode = false; // 重置编辑模式
        
        console.log('clearForm - 状态已重置');
    }

    // 获取表单数据中的文件
    getFormFiles() {
        return this.selectedFiles;
    }

    // 更新主列表中指定记录的附件数量显示
    async updateMainListAttachmentCount(recordId) {
        try {
            // 获取最新的附件数量
            const response = await fetch(`/api/v1/attachments/${recordId}`, {
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (!response.ok) {
                console.error('获取附件数量失败');
                return;
            }

            const attachments = await response.json();
            const attachmentCount = attachments.length;

            // 查找主列表中对应的行并更新附件数量显示
            const tableRows = document.querySelectorAll('#sales-table tbody tr');
            tableRows.forEach(row => {
                const editButton = row.querySelector('button[onclick*="showEditModal"]');
                if (editButton) {
                    const onclickAttr = editButton.getAttribute('onclick');
                    const match = onclickAttr.match(/showEditModal\('(\d+)'\)/);
                    if (match && match[1] === recordId.toString()) {
                        // 找到对应的行，更新附件数量
                        const attachmentCell = row.cells[10]; // 附件数量在第11列（索引10）
                        if (attachmentCell) {
                            const attachmentBadge = attachmentCount > 0 
                                ? `<span class="badge bg-primary">${attachmentCount}</span>` 
                                : '<span class="text-muted">-</span>';
                            attachmentCell.innerHTML = attachmentBadge;
                            console.log(`已更新记录 ${recordId} 的附件数量显示: ${attachmentCount}`);
                        }
                    }
                }
            });
        } catch (error) {
            console.error('更新主列表附件数量失败:', error);
        }
    }
}

// 创建全局实例
window.attachmentsManager = new AttachmentsManager();
console.log('AttachmentsManager已创建'); 