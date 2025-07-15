/**
 * 工作流程帮助系统
 * 提供销售订单管理流程的详细说明
 */

class WorkflowHelp {
    constructor() {
        this.initializeModal();
        this.attachEventListeners();
    }

    /**
     * 初始化模态框
     */
    initializeModal() {
        const modalHtml = `
            <div class="modal fade" id="workflowHelpModal" tabindex="-1" aria-labelledby="workflowHelpModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="workflowHelpModalLabel">
                                <i class="fas fa-info-circle text-primary"></i> 销售订单管理流程说明
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            ${this.getWorkflowContent()}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 如果模态框不存在，则添加到页面
        if (!document.getElementById('workflowHelpModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }
    }

    /**
     * 阶段标签高亮渲染
     */
    highlightStageLabels(html) {
        // 支持“阶段一”~“阶段五”
        const stageMap = {
            '阶段一': 'stage-label-1',
            '阶段二': 'stage-label-2',
            '阶段三': 'stage-label-3',
            '阶段四': 'stage-label-4',
            '阶段五': 'stage-label-5',
            '阶段1': 'stage-label-1',
            '阶段2': 'stage-label-2',
            '阶段3': 'stage-label-3',
            '阶段4': 'stage-label-4',
            '阶段5': 'stage-label-5',
        };
        return html.replace(/阶段[一二三四五12345]/g, txt => {
            const cls = stageMap[txt];
            return cls ? `<span class="stage-label ${cls}">${txt}</span>` : txt;
        });
    }

    /**
     * 获取工作流程内容
     */
    getWorkflowContent() {
        return this.highlightStageLabels(`
            <div class="workflow-help-content">
                <!-- 系统概述 -->
                <div class="section mb-4">
                    <h6 class="section-title">
                        <i class="fas fa-chart-line text-info"></i> 系统概述
                    </h6>
                    <div class="section-content">
                        <p>本系统是一个销售订单管理系统，主要用于管理美金订单的全生命周期流程。系统支持多种订单来源，包括阿里巴巴、国内客户和展会客户。</p>
                        <p>通过五个阶段的流程管理，确保订单从创建到最终完成的每个环节都得到有效控制和审核。</p>
                    </div>
                </div>

                <!-- 用户权限说明 -->
                <div class="section mb-4">
                    <h6 class="section-title">
                        <i class="fas fa-users text-warning"></i> 普通用户权限说明
                    </h6>
                    <div class="section-content">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="user-type-card">
                                    <div class="card-header">
                                        <i class="fas fa-user-tag text-success"></i> 销售用户
                                    </div>
                                    <div class="card-body">
                                        <ul class="permission-list">
                                            <li><i class="fas fa-check text-success"></i> 创建销售记录</li>
                                            <li><i class="fas fa-check text-success"></i> 在阶段一修改自己的记录</li>
                                            <li><i class="fas fa-check text-success"></i> 提交记录到阶段二</li>
                                            <li><i class="fas fa-check text-success"></i> 从阶段二撤回到阶段一</li>
                                            <li><i class="fas fa-check text-success"></i> 管理销售附件（仅阶段一）</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="user-type-card">
                                    <div class="card-header">
                                        <i class="fas fa-truck text-info"></i> 后勤用户
                                    </div>
                                    <div class="card-body">
                                        <ul class="permission-list">
                                            <li><i class="fas fa-check text-success"></i> 审核阶段二记录</li>
                                            <li><i class="fas fa-check text-success"></i> 在阶段三修改记录</li>
                                            <li><i class="fas fa-check text-success"></i> 提交记录到阶段四</li>
                                            <li><i class="fas fa-check text-success"></i> 撤回记录到阶段一或阶段三</li>
                                            <li><i class="fas fa-check text-success"></i> 管理后勤附件（仅阶段三）</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="user-type-card">
                                    <div class="card-header">
                                        <i class="fas fa-user-cog text-purple"></i> 销售+后勤用户
                                    </div>
                                    <div class="card-body">
                                        <ul class="permission-list">
                                            <li><i class="fas fa-check text-success"></i> 具备销售用户所有权限</li>
                                            <li><i class="fas fa-check text-success"></i> 具备后勤用户所有权限</li>
                                            <li><i class="fas fa-check text-success"></i> 可以管理所有类型附件</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 阶段说明（手风琴） -->
                <div class="section mb-4">
                    <h6 class="section-title">
                        <i class="fas fa-layer-group text-primary"></i> 阶段详细说明
                    </h6>
                    <div class="section-content">
                        <div class="stages-container accordion" id="workflowStageAccordion">
                            ${this.getStageAccordion()}
                        </div>
                    </div>
                </div>

                <!-- 流程图 -->
                <div class="section mb-4">
                    <h6 class="section-title">
                        <i class="fas fa-project-diagram text-success"></i> 流程状态转换图
                    </h6>
                    <div class="section-content">
                        <div class="workflow-diagram">
                            <div class="diagram-container">
                                <div class="stage-box stage-1-box">
                                    <div class="stage-icon">1</div>
                                    <div class="stage-name">信息录入</div>
                                    <div class="stage-status">待销售提交</div>
                                </div>
                                
                                <div class="arrow-container">
                                    <div class="arrow-line"></div>
                                    <div class="arrow-text">销售人员提交</div>
                                    <div class="arrow-head">→</div>
                                </div>
                                
                                <div class="stage-box stage-2-box">
                                    <div class="stage-icon">2</div>
                                    <div class="stage-name">初步审核</div>
                                    <div class="stage-status">待后勤审核</div>
                                </div>
                                
                                <div class="arrow-container">
                                    <div class="arrow-line"></div>
                                    <div class="arrow-text">后勤人员审核通过</div>
                                    <div class="arrow-head">→</div>
                                </div>
                                
                                <div class="stage-box stage-3-box">
                                    <div class="stage-icon">3</div>
                                    <div class="stage-name">信息补充</div>
                                    <div class="stage-status">待补充信息</div>
                                </div>
                                
                                <div class="arrow-container">
                                    <div class="arrow-line"></div>
                                    <div class="arrow-text">后勤人员提交</div>
                                    <div class="arrow-head">→</div>
                                </div>
                                
                                <div class="stage-box stage-4-box">
                                    <div class="stage-icon">4</div>
                                    <div class="stage-name">最终审核</div>
                                    <div class="stage-status">待最终审核</div>
                                </div>
                                
                                <div class="arrow-container">
                                    <div class="arrow-line"></div>
                                    <div class="arrow-text">高级用户审核通过</div>
                                    <div class="arrow-head">→</div>
                                </div>
                                
                                <div class="stage-box stage-5-box">
                                    <div class="stage-icon">5</div>
                                    <div class="stage-name">完成</div>
                                    <div class="stage-status">已完成</div>
                                </div>
                            </div>
                            
                            <!-- 撤回流程 -->
                            <div class="withdrawal-flows">
                                <div class="withdrawal-title">撤回流程：</div>
                                <div class="withdrawal-item">
                                    <span class="withdrawal-arrow">↙</span>
                                    <span class="withdrawal-text">阶段2→阶段1：销售人员可撤回</span>
                                </div>
                                <div class="withdrawal-item">
                                    <span class="withdrawal-arrow">↙</span>
                                    <span class="withdrawal-text">阶段3→阶段1：后勤人员可撤回</span>
                                </div>
                                <div class="withdrawal-item">
                                    <span class="withdrawal-arrow">↙</span>
                                    <span class="withdrawal-text">阶段4→阶段3：后勤人员可撤回</span>
                                </div>
                                <div class="withdrawal-item">
                                    <span class="withdrawal-arrow">↙</span>
                                    <span class="withdrawal-text">阶段5→阶段3：高级用户可撤回</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 附件管理说明 -->
                <div class="section mb-4">
                    <h6 class="section-title">
                        <i class="fas fa-paperclip text-secondary"></i> 附件管理说明
                    </h6>
                    <div class="section-content">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="attachment-type-card">
                                    <div class="card-header sales-attachment">
                                        <i class="fas fa-file-contract"></i> 销售附件
                                    </div>
                                    <div class="card-body">
                                        <p><strong>管理权限：</strong>销售人员（仅在阶段一）</p>
                                        <p><strong>包含内容：</strong></p>
                                        <ul>
                                            <li>销售合同</li>
                                            <li>订单确认书</li>
                                            <li>客户沟通记录</li>
                                            <li>产品规格书</li>
                                        </ul>
                                        <p><strong>注意事项：</strong>一旦提交到阶段二，销售附件将被锁定，无法修改或删除</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="attachment-type-card">
                                    <div class="card-header logistics-attachment">
                                        <i class="fas fa-file-invoice"></i> 后勤附件
                                    </div>
                                    <div class="card-body">
                                        <p><strong>管理权限：</strong>后勤人员（仅在阶段三）</p>
                                        <p><strong>包含内容：</strong></p>
                                        <ul>
                                            <li>采购发票</li>
                                            <li>运输单据</li>
                                            <li>报关文件</li>
                                            <li>费用明细</li>
                                        </ul>
                                        <p><strong>注意事项：</strong>只有在阶段三才能上传和管理后勤附件</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 操作提示 -->
                <div class="section">
                    <h6 class="section-title">
                        <i class="fas fa-lightbulb text-warning"></i> 操作提示
                    </h6>
                    <div class="section-content">
                        <div class="tips-container">
                            <div class="tip-item">
                                <i class="fas fa-info-circle text-info"></i>
                                <span>各阶段的操作权限严格控制，请确保在正确的阶段进行相应操作</span>
                            </div>
                            <div class="tip-item">
                                <i class="fas fa-exclamation-triangle text-warning"></i>
                                <span>附件一旦上传，请仔细检查，部分阶段无法修改</span>
                            </div>
                            <div class="tip-item">
                                <i class="fas fa-shield-alt text-success"></i>
                                <span>系统会自动保存操作记录，便于后续追踪和审计</span>
                            </div>
                            <div class="tip-item">
                                <i class="fas fa-clock text-primary"></i>
                                <span>建议及时处理待办事项，避免影响整体流程进度</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    /**
     * 阶段手风琴内容
     */
    getStageAccordion() {
        const stages = [
            {
                num: 1,
                title: '<span class="stage-label stage-label-1">阶段一</span> 信息录入阶段',
                color: 'stage-1',
                content: `<p><strong>状态：</strong>待销售提交</p>
                    <p><strong>操作者：</strong>销售人员</p>
                    <p><strong>主要工作：</strong></p>
                    <ul>
                        <li>录入订单基本信息（订单号、产品名称、数量、单价等）</li>
                        <li>上传销售相关附件（合同、订单确认书等）</li>
                        <li>补充完善订单详细信息</li>
                    </ul>
                    <p><strong>可用操作：</strong>修改、删除、提交、管理销售附件</p>`
            },
            {
                num: 2,
                title: '<span class="stage-label stage-label-2">阶段二</span> 初步审核阶段',
                color: 'stage-2',
                content: `<p><strong>状态：</strong>待后勤审核</p>
                    <p><strong>操作者：</strong>后勤人员</p>
                    <p><strong>主要工作：</strong></p>
                    <ul>
                        <li>审核订单信息的准确性</li>
                        <li>检查必要附件是否齐全</li>
                        <li>决定是否通过审核</li>
                    </ul>
                    <p><strong>可用操作：</strong>审核通过、撤回到阶段一</p>`
            },
            {
                num: 3,
                title: '<span class="stage-label stage-label-3">阶段三</span> 信息补充阶段',
                color: 'stage-3',
                content: `<p><strong>状态：</strong>待补充信息</p>
                    <p><strong>操作者：</strong>后勤人员</p>
                    <p><strong>主要工作：</strong></p>
                    <ul>
                        <li>补充运费、采购成本等信息</li>
                        <li>上传后勤相关附件（发票、运输单据等）</li>
                        <li>完善订单的所有财务信息</li>
                    </ul>
                    <p><strong>可用操作：</strong>修改、提交、管理后勤附件、撤回到阶段一</p>`
            },
            {
                num: 4,
                title: '<span class="stage-label stage-label-4">阶段四</span> 最终审核阶段',
                color: 'stage-4',
                content: `<p><strong>状态：</strong>待最终审核</p>
                    <p><strong>操作者：</strong>高级用户/管理员</p>
                    <p><strong>主要工作：</strong></p>
                    <ul>
                        <li>最终审核订单的完整性</li>
                        <li>确认财务信息的准确性</li>
                        <li>批准订单完成</li>
                    </ul>
                    <p><strong>可用操作：</strong>最终审核通过、撤回到阶段三</p>`
            },
            {
                num: 5,
                title: '<span class="stage-label stage-label-5">阶段五</span> 完成阶段',
                color: 'stage-5',
                content: `<p><strong>状态：</strong>已完成</p>
                    <p><strong>操作者：</strong>系统</p>
                    <p><strong>主要工作：</strong></p>
                    <ul>
                        <li>订单流程完成</li>
                        <li>可用于统计和报表</li>
                        <li>参与提成计算</li>
                    </ul>
                    <p><strong>可用操作：</strong>查看（高级用户可撤回到阶段三）</p>`
            }
        ];
        return stages.map((stage, idx) => `
            <div class="stage-card ${stage.color} mb-2">
                <div class="stage-header accordion-header d-flex align-items-center" style="cursor:pointer;" data-stage-idx="${idx}">
                    <span class="stage-number">${stage.num}</span>
                    <span class="stage-title">${stage.title}</span>
                    <span class="ms-auto"><i class="fas fa-chevron-down stage-chevron"></i></span>
                </div>
                <div class="stage-content collapse" id="stage-content-${idx}">
                    ${stage.content}
                </div>
            </div>
        `).join('');
    }

    /**
     * 绑定事件监听器
     */
    attachEventListeners() {
        // 监听帮助按钮点击事件
        document.addEventListener('click', (e) => {
            if (e.target.closest('.workflow-help-btn')) {
                this.showModal();
            }
            // 阶段手风琴点击
            const header = e.target.closest('.stage-header');
            if (header && header.hasAttribute('data-stage-idx')) {
                const idx = header.getAttribute('data-stage-idx');
                const content = document.getElementById(`stage-content-${idx}`);
                const chevron = header.querySelector('.stage-chevron');
                if (content.classList.contains('show')) {
                    content.classList.remove('show');
                    chevron.style.transform = '';
                } else {
                    content.classList.add('show');
                    chevron.style.transform = 'rotate(180deg)';
                }
            }
        });
    }

    /**
     * 显示模态框
     */
    showModal() {
        const modal = new bootstrap.Modal(document.getElementById('workflowHelpModal'));
        modal.show();
    }

    /**
     * 创建帮助按钮
     */
    static createHelpButton() {
        return `
            <button type="button" class="btn btn-outline-info workflow-help-btn" title="查看流程说明">
                <i class="fas fa-question-circle"></i>
                <span class="help-btn-text">流程说明</span>
            </button>
        `;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工作流程帮助系统
    window.workflowHelp = new WorkflowHelp();
    
    // 自动在左侧添加帮助按钮（如果容器存在）
    const helpContainer = document.querySelector('.workflow-help-container');
    if (helpContainer) {
        helpContainer.innerHTML = WorkflowHelp.createHelpButton();
    }
}); 