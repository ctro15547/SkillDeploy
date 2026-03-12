// ==========================================
// API 调用函数
// ==========================================

/**
 * 获取工具列表
 */
async function fetchTools() {
    try {
        const response = await fetch('/api/tools');
        if (!response.ok) throw new Error('获取工具列表失败');
        return await response.json();
    } catch (error) {
        console.error('fetchTools error:', error);
        showToast('获取工具列表失败', 'error');
        return [];
    }
}

// ==========================================
// 页面切换逻辑
// ==========================================

// DOM Elements
const skillsPageTab = document.getElementById('skillsPageTab');
const agentPageTab = document.getElementById('agentPageTab');
const skillsPageView = document.getElementById('skillsPageView');
const agentPageView = document.getElementById('agentPageView');

// Function to show the Skills view
function showSkillsView() {
    skillsPageView.classList.add('active');
    agentPageView.setAttribute('hidden', '');
    skillsPageTab.setAttribute('aria-selected', 'true');
    agentPageTab.setAttribute('aria-selected', 'false');
    skillsPageTab.classList.add('active');
    agentPageTab.classList.remove('active');
}

// Function to show the Agent view
function showAgentView() {
    skillsPageView.classList.remove('active');
    agentPageView.removeAttribute('hidden');
    agentPageTab.setAttribute('aria-selected', 'true');
    skillsPageTab.setAttribute('aria-selected', 'false');
    agentPageTab.classList.add('active');
    skillsPageTab.classList.remove('active');
}

// Event Listeners for tab clicks are added in bindEvents()
// ==========================================


/**
 * 获取技能列表
 */
async function fetchSkills() {
    try {
        const response = await fetch('/api/skills');
        if (!response.ok) throw new Error('获取技能列表失败');
        return await response.json();
    } catch (error) {
        console.error('fetchSkills error:', error);
        showToast('获取技能列表失败', 'error');
        return [];
    }
}

/**
 * 获取技能列表
 */
async function fetchSkills() {
    try {
        const response = await fetch('/api/skills');
        if (!response.ok) throw new Error('获取技能列表失败');
        return await response.json();
    } catch (error) {
        console.error('fetchSkills error:', error);
        showToast('获取技能列表失败', 'error');
        return [];
    }
}

/**
 * 获取工具目录下的技能列表
 */
async function fetchToolSkills(toolId) {
    try {
        const response = await fetch(`/api/tools/${toolId}/skills`);
        if (!response.ok) throw new Error('获取工具技能列表失败');
        return await response.json();
    } catch (error) {
        console.error('fetchToolSkills error:', error);
        return [];
    }
}

/**
 * 添加新工具
 */
async function addTool(toolData) {
    try {
        const response = await fetch('/api/tools', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(toolData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '添加工具失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('addTool error:', error);
        throw error;
    }
}

/**
 * 删除工具
 */
async function deleteTool(toolId) {
    try {
        const response = await fetch(`/api/tools/${toolId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '删除工具失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('deleteTool error:', error);
        throw error;
    }
}



const state = {
    tools: [],
    skills: [],
    selectedTool: null,
    selectedSkills: new Set(),
    distributionMethod: 'copy',
    searchQuery: '',
    currentPage: 'skills',
    toolSkillsCache: {}  // 缓存每个工具的已有技能列表，key 为 toolId
};

async function init() {
    state.tools = await fetchTools();
    state.skills = await fetchSkills();
    await renderTools();
    renderSkills();
    updateCounts();
    bindEvents();
    detectSystemRecommendation();
}

async function renderTools() {
    const container = document.getElementById('toolsContainer');

    // 先渲染工具卡片框架
    container.innerHTML = state.tools.map(tool => `
        <div class="card tool-card" data-tool-id="${tool.id}">
            <div class="tool-card-header">
                <div class="tool-header-left" onclick="selectTool('${tool.id}')">
                    <span class="tool-icon">📦</span>
                    <span class="tool-name">${tool.name}</span>
                </div>
                <button class="btn-icon-small delete-btn" onclick="event.stopPropagation(); handleDeleteTool('${tool.id}', '${tool.name}')" title="删除工具">🗑️</button>
            </div>
            <div class="tool-path" onclick="selectTool('${tool.id}')">${tool.skills_dir || tool.path}</div>

            <div class="tool-skills" onclick="selectTool('${tool.id}')">
                <div class="tool-skills-header">
                    <span>已有技能 <span id="tool-skills-count-${tool.id}">...</span></span>
                    <button class="btn-icon-small delete-btn tool-skill-batch-del-btn" id="batch-del-btn-${tool.id}"
                        style="display:none" title="删除选中技能"
                        onclick="event.stopPropagation(); handleBatchDeleteToolSkills('${tool.id}')">
                        <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                            <polyline points="1,3 11,3"/><path d="M2,3l.7,7.3a1,1,0,0,0,1,.7H8.3a1,1,0,0,0,1-.7L10,3"/><line x1="4.5" y1="5.5" x2="4.5" y2="9"/><line x1="7.5" y1="5.5" x2="7.5" y2="9"/><path d="M4,3V2a1,1,0,0,1,1-1H7a1,1,0,0,1,1,1V3"/>
                        </svg>
                        删除选中
                    </button>
                </div>
                <div class="tool-skills-list" id="tool-skills-list-${tool.id}">
                    <div class="empty-state">加载中...</div>
                </div>
            </div>

            <div class="tool-method" onclick="selectTool('${tool.id}')">
                <span>${getMethodIcon(tool.distribute_method || tool.distribution_method)}</span>
                <span>${getMethodText(tool.distribute_method || tool.distribution_method)}</span>
            </div>
        </div>
    `).join('');

    // 异步加载每个工具的技能，并缓存
    for (const tool of state.tools) {
        const toolSkills = await fetchToolSkills(tool.id);
        state.toolSkillsCache[tool.id] = toolSkills;
        const countElement = document.getElementById(`tool-skills-count-${tool.id}`);
        const listElement = document.getElementById(`tool-skills-list-${tool.id}`);

        if (countElement) {
            countElement.textContent = `(${toolSkills.length})`;
        }

        if (listElement) {
            if (toolSkills.length > 0) {
                listElement.innerHTML = toolSkills.map(skill =>
                    `<div class="skill-tag-row" data-skill-id="${skill.id}">
                        <label class="skill-tag-check-label">
                            <input type="checkbox" class="tool-skill-checkbox" data-tool-id="${tool.id}" data-skill-id="${skill.id}"
                                onchange="onToolSkillCheckChange(this, '${tool.id}')">
                            <span class="skill-tag">${skill.name}</span>
                        </label>
                        <button class="tool-skill-del-btn" title="删除此技能" aria-label="删除技能 ${skill.name}"
                            onclick="event.stopPropagation(); handleDeleteToolSkill('${tool.id}', '${skill.id}', '${skill.name}')">
                            <svg class="del-icon" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                                <polyline points="1,3 11,3"/><path d="M2,3l.7,7.3a1,1,0,0,0,1,.7H8.3a1,1,0,0,0,1-.7L10,3"/><line x1="4.5" y1="5.5" x2="4.5" y2="9"/><line x1="7.5" y1="5.5" x2="7.5" y2="9"/><path d="M4,3V2a1,1,0,0,1,1-1H7a1,1,0,0,1,1,1V3"/>
                            </svg>
                        </button>
                    </div>`
                ).join('');
            } else {
                listElement.innerHTML = '<div class="empty-state">暂无技能</div>';
            }
        }
    }
}

function renderSkills() {
    const container = document.getElementById('skillsContainer');
    const filteredSkills = state.skills.filter(skill =>
        skill.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
        (skill.description || '').toLowerCase().includes(state.searchQuery.toLowerCase())
    );
    
    // 超过6个技能时切换为多列（最多3列），否则保持单列
    if (filteredSkills.length > 6) {
        container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(160px, 1fr))';
    } else {
        container.style.gridTemplateColumns = '1fr';
    }

    container.innerHTML = filteredSkills.map(skill => `
        <div class="card skill-card" data-skill-id="${skill.id}">
            <div class="skill-name">${skill.name}</div>
            <div class="skill-source ${skill.source}">
                <span>${skill.source === 'git' ? '📦' : '✏️'}</span>
                <span>${skill.source === 'git' ? 'Git来源' : '手动添加'}</span>
            </div>
            <div class="skill-description">${skill.description}</div>
            <div class="skill-path" title="${skill.path}">${skill.path}</div>
        </div>
    `).join('');
}

function applyDistributionMethod(method) {
    const normalizedMethod = ['auto', 'symlink', 'copy'].includes(method) ? method : 'copy';
    state.distributionMethod = normalizedMethod;

    document.querySelectorAll('.method-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.method === normalizedMethod);
        btn.setAttribute('aria-pressed', btn.dataset.method === normalizedMethod ? 'true' : 'false');
    });
}

function selectTool(toolId) {
    state.selectedTool = toolId;

    document.querySelectorAll('.tool-card').forEach(card => {
        card.classList.remove('selected');
    });

    const selectedCard = document.querySelector(`[data-tool-id="${toolId}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }

    const select = document.getElementById('targetTool');
    select.value = toolId;

    const tool = state.tools.find(t => String(t.id) === String(toolId));
    applyDistributionMethod(tool?.distribute_method || tool?.distribution_method);

    updateExecuteButton();
}

// 暴露到全局作用域，供 HTML onclick 调用
window.selectTool = selectTool;

function toggleSkill(skillId) {
    // 统一转字符串，避免数字/字符串类型不一致导致 Set.has() 匹配失败
    const id = String(skillId);
    if (state.selectedSkills.has(id)) {
        state.selectedSkills.delete(id);
    } else {
        state.selectedSkills.add(id);
    }

    // 同步卡片选中样式
    const card = document.querySelector(`[data-skill-id="${id}"]`);
    if (card) card.classList.toggle('selected', state.selectedSkills.has(id));

    updateSelectedSkillsDisplay();
    updateExecuteButton();
}

// 暴露到全局作用域，供 HTML onchange 调用
window.toggleSkill = toggleSkill;

function updateSelectedSkillsDisplay() {
    const container = document.getElementById('selectedSkills');
    const countBadge = document.getElementById('selectedCount');
    
    countBadge.textContent = state.selectedSkills.size;
    
    if (state.selectedSkills.size === 0) {
        container.innerHTML = '<span class="empty-hint">未选择任何技能</span>';
        return;
    }
    
    const selectedSkillsArray = Array.from(state.selectedSkills).map(id => {
        const skill = state.skills.find(s => String(s.id) === String(id));
        return skill ? skill.name : id;
    });
    
    container.innerHTML = selectedSkillsArray.map(name => `
        <span class="skill-tag">${name}</span>
    `).join('');
}

function updateExecuteButton() {
    const btn = document.getElementById('executeBtn');
    const canExecute = state.selectedTool && state.selectedSkills.size > 0;
    const duplicates = checkDuplicateSkills();

    if (canExecute && duplicates.length > 0) {
        // 有重名技能，禁用按钮并提示
        btn.disabled = true;
        btn.title = `存在重名技能: ${duplicates.join('、')}`;
        showToast(`已选技能与目标工具已有技能重名: ${duplicates.join('、')}，不允许分发`, 'warning');
    } else {
        btn.disabled = !canExecute;
        btn.title = '';
    }
}

/**
 * 检测已选技能与目标工具已有技能是否存在重名
 * 返回重名的技能名称数组
 */
function checkDuplicateSkills() {
    if (!state.selectedTool || state.selectedSkills.size === 0) {
        return [];
    }

    const toolSkills = state.toolSkillsCache[state.selectedTool] || [];
    if (toolSkills.length === 0) {
        return [];
    }

    // 工具已有技能名称集合（小写比较，避免大小写差异遗漏）
    const existingNames = new Set(toolSkills.map(s => s.name.toLowerCase()));

    // 已选技能中与已有技能重名的
    const duplicates = [];
    for (const skillId of state.selectedSkills) {
        const skill = state.skills.find(s => String(s.id) === String(skillId));
        if (skill && existingNames.has(skill.name.toLowerCase())) {
            duplicates.push(skill.name);
        }
    }

    return duplicates;
}

function updateCounts() {
    document.getElementById('toolsCount').textContent = state.tools.length;
    document.getElementById('skillsCount').textContent = state.skills.length;
}

function switchPage(page) {
    const normalizedPage = page === 'agent' ? 'agent' : 'skills';
    state.currentPage = normalizedPage;

    document.querySelectorAll('.page-tab').forEach(tab => {
        const isActive = tab.dataset.page === normalizedPage;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('.page-view').forEach(view => {
        const shouldShow = view.id === `${normalizedPage}PageView`;
        view.classList.toggle('active', shouldShow);
        view.hidden = !shouldShow;
    });

    const distributionPanel = document.getElementById('distributionPanel');
    if (distributionPanel) {
        distributionPanel.hidden = normalizedPage !== 'skills';
    }

    // 切换到 Agent 页面时加载数据
    if (normalizedPage === 'agent') {
        loadAgentPageData();
    }
}

function getMethodIcon(method) {
    const icons = {
        'auto': '⚡',
        'symlink': '🔗',
        'copy': '📋',
        'smart': '🔍'   // 混合模式：软链接+拷贝并存
    };
    return icons[method] || '📋';
}

function getMethodText(method) {
    const texts = {
        'auto': '自动',
        'symlink': '软链接',
        'copy': '拷贝',
        'smart': '智能检测'  // 目录内软链接和拷贝混合存在
    };
    return texts[method] || '拷贝';
}

function detectSystemRecommendation() {
    const platform = navigator.platform.toLowerCase();
    let recommendation = '软链接';
    
    if (platform.includes('win')) {
        recommendation = '拷贝';
    }
    
    document.getElementById('systemRecommendation').textContent = `系统推荐: ${recommendation}`;
}

function bindEvents() {
    document.querySelectorAll('.page-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchPage(tab.dataset.page);
        });
    });

    document.getElementById('targetTool').addEventListener('change', (e) => {
        if (e.target.value) {
            selectTool(e.target.value);
        }
    });
    
    const select = document.getElementById('targetTool');
    select.innerHTML = '<option value="">请选择工具...</option>' + 
        state.tools.map(tool => `<option value="${tool.id}">${tool.name}</option>`).join('');
    
    document.querySelectorAll('.method-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.method-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.distributionMethod = btn.dataset.method;
        });
    });

    // 初始化时同步按钮 active 状态，确保与 state.distributionMethod 一致（默认拷贝）
    document.querySelectorAll('.method-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.method === state.distributionMethod);
    });
    console.log('[DEBUG] bindEvents 初始化完成，state.distributionMethod =', state.distributionMethod);
    console.log('[DEBUG] 初始化后激活的按钮 =', document.querySelector('.method-btn.active')?.dataset?.method);
    
    document.getElementById('skillSearch').addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        renderSkills();
    });

    // 技能卡片点击事件委托：点击卡片任意区域均可选中/取消技能
    document.getElementById('skillsContainer').addEventListener('click', (e) => {
        const card = e.target.closest('.skill-card');
        if (!card) return;
        const skillId = card.dataset.skillId;
        if (skillId) toggleSkill(skillId);
    });
    
    document.getElementById('cancelBtn').addEventListener('click', () => {
        resetSelection();
    });
    
    document.getElementById('previewBtn').addEventListener('click', () => {
        showPreview();
    });
    
    document.getElementById('executeBtn').addEventListener('click', () => {
        showPreview();
    });
    
    document.getElementById('closePreview').addEventListener('click', () => {
        closeModal('previewModal');
    });
    
    document.getElementById('cancelPreview').addEventListener('click', () => {
        closeModal('previewModal');
    });
    
    document.getElementById('confirmExecute').addEventListener('click', () => {
        executeDistribution();
    });
    
    document.getElementById('refreshBtn').addEventListener('click', async () => {
        showToast('正在刷新数据...', 'info');

        // 重新加载数据
        state.tools = await fetchTools();
        state.skills = await fetchSkills();

        // 刷新界面
        await renderTools();
        renderSkills();
        updateCounts();

        // 更新下拉选择框
        const select = document.getElementById('targetTool');
        select.innerHTML = '<option value="">请选择工具...</option>' +
            state.tools.map(tool => `<option value="${tool.id}">${tool.name}</option>`).join('');

        showToast('数据已刷新', 'success');
    });
    
    document.getElementById('settingsBtn').addEventListener('click', () => {
        showToast('设置功能开发中...', 'info');
    });
    
    document.getElementById('helpBtn').addEventListener('click', () => {
        showToast('帮助文档开发中...', 'info');
    });
    
    document.getElementById('addToolBtn').addEventListener('click', () => {
        document.getElementById('addToolModal').classList.add('show');
    });
    
    document.getElementById('closeAddTool').addEventListener('click', closeAddToolModal);
    document.getElementById('cancelAddTool').addEventListener('click', closeAddToolModal);
    
    document.getElementById('confirmAddTool').addEventListener('click', async () => {
        const form = document.getElementById('addToolForm');
        if (form.checkValidity()) {
            await handleAddTool();
        } else {
            form.reportValidity();
        }
    });
    
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });

    switchPage(state.currentPage);

    // 绑定 Agent 页面事件
    bindAgentEvents();
}

function closeAddToolModal() {
    document.getElementById('addToolModal').classList.remove('show');
    document.getElementById('addToolForm').reset();
}

async function handleAddTool() {
    const form = document.getElementById('addToolForm');
    const formData = new FormData(form);
    const toolData = {
        id: `tool_${Date.now()}`,
        name: formData.get('name'),
        skills_dir: formData.get('skills_dir'),
        enabled: true,
        distribute_method: formData.get('distribute_method'),
        // agent_path 可选，为空字符串时不传
        ...(formData.get('agent_path') ? { agent_path: formData.get('agent_path') } : {}),
    };

    try {
        console.log('添加工具:', toolData);
        await addTool(toolData);
        showToast('工具添加成功', 'success');
        closeAddToolModal();

        // 重新加载数据
        state.tools = await fetchTools();
        state.skills = await fetchSkills();

        // 刷新界面
        await renderTools();
        renderSkills();
        updateCounts();

        // 更新下拉选择框
        const select = document.getElementById('targetTool');
        select.innerHTML = '<option value="">请选择工具...</option>' +
            state.tools.map(tool => `<option value="${tool.id}">${tool.name}</option>`).join('');

        // 如果当前在 Agent 页面，同步刷新 Agent 工具列表
        if (state.currentPage === 'agent') {
            await loadAgentPageData();
        }

        console.log('工具添加完成，界面已刷新');
    } catch (error) {
        console.error('添加工具失败:', error);
        showToast(error.message || '添加工具失败', 'error');
    }
}

async function handleDeleteTool(toolId, toolName) {
    if (!confirm(`确定要删除工具"${toolName}"吗？`)) {
        return;
    }

    try {
        console.log('删除工具:', toolId);
        await deleteTool(toolId);
        showToast('工具删除成功', 'success');

        // 重新加载数据
        state.tools = await fetchTools();
        state.skills = await fetchSkills();

        // 刷新界面
        await renderTools();
        renderSkills();
        updateCounts();

        // 更新下拉选择框
        const select = document.getElementById('targetTool');
        select.innerHTML = '<option value="">请选择工具...</option>' +
            state.tools.map(tool => `<option value="${tool.id}">${tool.name}</option>`).join('');

        // 如果删除的是当前选中的工具，清空选择
        if (state.selectedTool === toolId) {
            state.selectedTool = null;
            state.selectedSkills.clear();
            updateSelectedSkillsDisplay();
            updateExecuteButton();
        }

        console.log('工具删除完成，界面已刷新');
    } catch (error) {
        console.error('删除工具失败:', error);
        showToast(error.message || '删除工具失败', 'error');
    }
}

window.handleDeleteTool = handleDeleteTool;

function resetSelection() {
    state.selectedTool = null;
    state.selectedSkills.clear();
    
    document.querySelectorAll('.tool-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    document.getElementById('targetTool').value = '';
    
    renderSkills();
    updateSelectedSkillsDisplay();
    updateExecuteButton();
    
    showToast('已重置选择', 'info');
}

function showPreview() {
    // 调试：打印当前分发方式状态
    console.log('[DEBUG] showPreview 调用时 state.distributionMethod =', state.distributionMethod);
    console.log('[DEBUG] 当前激活的按钮 =', document.querySelector('.method-btn.active')?.dataset?.method);

    if (!state.selectedTool || state.selectedSkills.size === 0) {
        showToast('请选择工具和技能', 'warning');
        return;
    }

    // 重名检测
    const duplicates = checkDuplicateSkills();
    if (duplicates.length > 0) {
        showToast(`已选技能与目标工具已有技能重名: ${duplicates.join('、')}，不允许分发`, 'warning');
        return;
    }

    const tool = state.tools.find(t => t.id === state.selectedTool);
    const skills = Array.from(state.selectedSkills).map(id => 
        state.skills.find(s => s.id === id)
    );
    
    const cleanBrokenLinks = document.getElementById('cleanBrokenLinks').checked;
    const cleanUnused = document.getElementById('cleanUnused').checked;
    const backupExisting = document.getElementById('backupExisting').checked;
    
    const previewContent = document.getElementById('previewContent');
    previewContent.innerHTML = `
        <div class="preview-section">
            <h4>目标工具</h4>
            <div class="preview-item">
                <span class="preview-label">工具名称:</span>
                <span class="preview-value">${tool.name}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">目标路径:</span>
                <span class="preview-value">${tool.skills_dir || tool.path}</span>
            </div>
        </div>
        
        <div class="preview-section">
            <h4>待分发技能 (${skills.length})</h4>
            ${skills.map(skill => `
                <div class="preview-skill">
                    <span class="preview-skill-name">${skill.name}</span>
                    <span class="preview-skill-path">${skill.path}</span>
                </div>
            `).join('')}
        </div>
        
        <div class="preview-section">
            <h4>分发方式</h4>
            <div class="preview-item">
                <span class="preview-label">方法:</span>
                <span class="preview-value">${getMethodText(state.distributionMethod)}</span>
            </div>
        </div>
        
        <div class="preview-section">
            <h4>清理选项</h4>
            <div class="preview-item">
                <span class="preview-label">清理失效软链接:</span>
                <span class="preview-value">${cleanBrokenLinks ? '是' : '否'}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">清理未使用技能:</span>
                <span class="preview-value">${cleanUnused ? '是' : '否'}</span>
            </div>
            <div class="preview-item">
                <span class="preview-label">备份现有文件:</span>
                <span class="preview-value">${backupExisting ? '是' : '否'}</span>
            </div>
        </div>
    `;
    
    document.getElementById('previewModal').style.display = 'flex';
    // 调试：打印实际渲染到弹窗里的分发方式文字
    const renderedMethod = document.querySelector('#previewContent .preview-value');
    console.log('[DEBUG] 弹窗渲染后第一个 preview-value =', renderedMethod?.textContent);
    console.log('[DEBUG] previewContent 完整HTML =', document.getElementById('previewContent')?.innerHTML?.substring(0, 500));
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

async function executeDistribution() {
    // 分发前再次检查重名
    const duplicates = checkDuplicateSkills();
    if (duplicates.length > 0) {
        closeModal('previewModal');
        showToast(`已选技能与目标工具已有技能重名: ${duplicates.join('、')}，不允许分发`, 'warning');
        return;
    }

    closeModal('previewModal');
    showToast('正在执行分发...', 'info');

    try {
        const response = await fetch('/api/distribute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tool_ids: [state.selectedTool],
                skill_ids: Array.from(state.selectedSkills),
                force: false,
                distribute_method: state.distributionMethod
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || '分发请求失败');
        }

        // 刷新工具技能列表
        await renderTools();
        resetSelection();

        const type = result.success ? 'success' : 'warning';
        showToast(result.message, type);
    } catch (error) {
        console.error('executeDistribution error:', error);
        showToast(`分发失败: ${error.message}`, 'error');
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toast.className = `toast ${type}`;
    toastMessage.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

document.addEventListener('DOMContentLoaded', init);

// ==================== 工具技能删除 ====================

/**
 * checkbox 变化时：更新行高亮 + 批量删除按钮显示
 */
function onToolSkillCheckChange(checkbox, toolId) {
    // 切换当前行的选中高亮
    const row = checkbox.closest('.skill-tag-row');
    if (row) {
        row.classList.toggle('is-checked', checkbox.checked);
    }
    // 更新批量删除按钮
    const checkboxes = document.querySelectorAll(
        `#tool-skills-list-${toolId} .tool-skill-checkbox:checked`
    );
    const btn = document.getElementById(`batch-del-btn-${toolId}`);
    if (btn) {
        btn.style.display = checkboxes.length > 0 ? 'inline-flex' : 'none';
    }
}

/**
 * 删除单个工具技能，弹窗确认
 */
async function handleDeleteToolSkill(toolId, skillId, skillName) {
    if (!confirm(`确认删除工具下的技能「${skillName}」？\n此操作将删除本地文件/软链接，不可恢复。`)) {
        return;
    }
    try {
        const res = await fetch(`/api/tools/${toolId}/skills/${skillId}`, { method: 'DELETE' });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || '删除失败');
        showToast(`已删除技能: ${skillName}`, 'success');
        // 刷新该工具的技能列表
        await refreshToolSkills(toolId);
    } catch (error) {
        console.error('handleDeleteToolSkill error:', error);
        showToast(`删除失败: ${error.message}`, 'error');
    }
}

/**
 * 批量删除选中的工具技能，弹窗确认
 */
async function handleBatchDeleteToolSkills(toolId) {
    const checkboxes = document.querySelectorAll(
        `#tool-skills-list-${toolId} .tool-skill-checkbox:checked`
    );
    if (checkboxes.length === 0) return;

    const skillIds = Array.from(checkboxes).map(cb => cb.dataset.skillId);
    const skillNames = Array.from(checkboxes).map(cb => {
        const tag = cb.closest('.skill-tag-row')?.querySelector('.skill-tag');
        return tag ? tag.textContent : cb.dataset.skillId;
    });

    if (!confirm(`确认删除以下 ${skillIds.length} 个技能？\n${skillNames.join('、')}\n\n此操作将删除本地文件/软链接，不可恢复。`)) {
        return;
    }

    let successCount = 0;
    let failCount = 0;
    for (let i = 0; i < skillIds.length; i++) {
        try {
            const res = await fetch(`/api/tools/${toolId}/skills/${skillIds[i]}`, { method: 'DELETE' });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '删除失败');
            }
            successCount++;
        } catch (error) {
            console.error(`删除技能 ${skillIds[i]} 失败:`, error);
            failCount++;
        }
    }

    showToast(
        failCount === 0
            ? `已删除 ${successCount} 个技能`
            : `删除完成: 成功 ${successCount}, 失败 ${failCount}`,
        failCount === 0 ? 'success' : 'warning'
    );
    await refreshToolSkills(toolId);
}

/**
 * 刷新单个工具的技能列表（不重绘整个工具列表）
 */
async function refreshToolSkills(toolId) {
    const toolSkills = await fetchToolSkills(toolId);
    state.toolSkillsCache[toolId] = toolSkills;
    const countElement = document.getElementById(`tool-skills-count-${toolId}`);
    const listElement = document.getElementById(`tool-skills-list-${toolId}`);
    const batchBtn = document.getElementById(`batch-del-btn-${toolId}`);

    if (countElement) countElement.textContent = `(${toolSkills.length})`;
    if (batchBtn) batchBtn.style.display = 'none';

    if (listElement) {
        if (toolSkills.length > 0) {
            listElement.innerHTML = toolSkills.map(skill =>
                `<div class="skill-tag-row" data-skill-id="${skill.id}">
                    <label class="skill-tag-check-label">
                        <input type="checkbox" class="tool-skill-checkbox" data-tool-id="${toolId}" data-skill-id="${skill.id}"
                            onchange="onToolSkillCheckChange(this, '${toolId}')">
                        <span class="skill-tag">${skill.name}</span>
                    </label>
                    <button class="tool-skill-del-btn" title="删除此技能" aria-label="删除技能 ${skill.name}"
                        onclick="event.stopPropagation(); handleDeleteToolSkill('${toolId}', '${skill.id}', '${skill.name}')">
                        <svg class="del-icon" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                            <polyline points="1,3 11,3"/><path d="M2,3l.7,7.3a1,1,0,0,0,1,.7H8.3a1,1,0,0,0,1-.7L10,3"/><line x1="4.5" y1="5.5" x2="4.5" y2="9"/><line x1="7.5" y1="5.5" x2="7.5" y2="9"/><path d="M4,3V2a1,1,0,0,1,1-1H7a1,1,0,0,1,1,1V3"/>
                        </svg>
                    </button>
                </div>`
            ).join('');
        } else {
            listElement.innerHTML = '<div class="empty-state">暂无技能</div>';
        }
    }
}


// ==========================================
// Agent 页面状态
// ==========================================

const agentState = {
    tools: [],           // AgentStatus 列表（各工具 Agent 状态）
    library: [],         // AgentFile 列表（Agent 库文件）
    selectedToolIds: new Set(),   // 已勾选的目标工具 ID（多选）
    selectedFiles: new Set(),     // 已选的 Agent 库文件名（多选）
    distributeMethod: 'copy',     // 分发方式
    // 兼容旧引用
    get selectedFile() { return this.selectedFiles.size > 0 ? [...this.selectedFiles][0] : null; },
};

// ==========================================
// Agent 页面 API 调用
// ==========================================

/**
 * 获取 Agent 库文件列表
 */
async function fetchAgentLibrary() {
    try {
        const response = await fetch('/api/agent/library');
        if (!response.ok) throw new Error('获取 Agent 库失败');
        return await response.json();
    } catch (error) {
        console.error('fetchAgentLibrary error:', error);
        showToast('获取 Agent 库失败', 'error');
        return [];
    }
}

/**
 * 获取指定工具的 Agent 状态
 * 无 agent_path 配置时返回占位状态（而非 null），确保 Agent 页面能显示所有工具
 */
async function fetchToolAgentStatus(toolId) {
    try {
        const response = await fetch(`/api/tools/${toolId}/agent`);
        if (response.status === 404) {
            // 无 agent_path 配置，构造占位状态
            const tool = state.tools.find(t => t.id === toolId);
            return {
                tool_id: toolId,
                tool_name: tool ? tool.name : toolId,
                agent_path: '',
                exists: false,
                is_symlink: false,
                symlink_target: null,
                file_size: null,
                modified_time: null,
                no_agent_path: true,  // 标记：未配置 agent_path
            };
        }
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error(`fetchToolAgentStatus(${toolId}) error:`, error);
        return null;
    }
}

/**
 * 加载 Agent 页面所有数据（工具状态 + Agent 库）
 */
async function loadAgentPageData() {
    console.log('[Agent] 加载页面数据...');

    // 并行加载 Agent 库和所有工具状态
    const [library, tools] = await Promise.all([
        fetchAgentLibrary(),
        fetchAllToolsAgentStatus(),
    ]);

    agentState.library = library;
    agentState.tools = tools;

    renderAgentTools();
    renderAgentLibrary();
    updateAgentDistributionPanel();

    document.getElementById('agentToolsCount').textContent = tools.length;
    document.getElementById('agentLibraryCount').textContent = library.length;
    console.log(`[Agent] 数据加载完成：${tools.length} 个工具，${library.length} 个 Agent 文件`);
}

/**
 * 获取所有工具的 Agent 状态（并行请求）
 */
async function fetchAllToolsAgentStatus() {
    try {
        // 复用 Skills 页面已加载的工具列表
        const tools = state.tools.length > 0 ? state.tools : await fetchTools();
        const requests = tools
            .filter(t => t.enabled !== false)
            .map(t => fetchToolAgentStatus(t.id));
        const results = await Promise.all(requests);
        // 过滤掉无 agent_path 配置的工具（返回 null）
        return results.filter(Boolean);
    } catch (error) {
        console.error('fetchAllToolsAgentStatus error:', error);
        return [];
    }
}

// ==========================================
// Agent 页面渲染
// ==========================================

/**
 * 渲染工具列表（左侧面板）
 */
function renderAgentTools() {
    const container = document.getElementById('agentToolsContainer');
    if (!container) return;

    if (agentState.tools.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无工具配置</div>';
        return;
    }

    container.innerHTML = agentState.tools.map(status => {
        const isSelected = agentState.selectedToolIds.has(status.tool_id);
        const hasFile = status.exists;

        // 状态标签
        let statusBadge = '';
        if (status.no_agent_path) {
            statusBadge = '<span class="agent-status-badge agent-status-none">未配置路径</span>';
        } else if (!hasFile) {
            statusBadge = '<span class="agent-status-badge agent-status-none">未配置</span>';
        } else if (status.is_symlink) {
            statusBadge = '<span class="agent-status-badge agent-status-symlink">🔗 软链接</span>';
        } else {
            statusBadge = '<span class="agent-status-badge agent-status-exists">✓ 已配置</span>';
        }

        // 文件信息：无 agent_path 时显示提示
        let fileInfo = '';
        if (status.no_agent_path) {
            fileInfo = `<div class="agent-tool-fileinfo" style="opacity:0.5;">请在工具配置中添加 agent_path</div>`;
        } else if (hasFile) {
            const size = status.file_size ? formatFileSize(status.file_size) : '';
            const mtime = status.modified_time
                ? new Date(status.modified_time).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
                : '';
            fileInfo = `<div class="agent-tool-fileinfo">${size}${size && mtime ? ' · ' : ''}${mtime}</div>`;
            if (status.is_symlink && status.symlink_target) {
                fileInfo += `<div class="agent-tool-symlink-target" title="${status.symlink_target}">→ ${status.symlink_target}</div>`;
            }
        }

        return `
        <div class="card agent-tool-card ${isSelected ? 'selected' : ''}" data-tool-id="${status.tool_id}"
            onclick="toggleAgentTool('${status.tool_id}')"
            role="checkbox" tabindex="0" aria-checked="${isSelected}"
            onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleAgentTool('${status.tool_id}')}">
            <div class="agent-tool-card-header">
                <label class="agent-tool-check-label" onclick="event.stopPropagation()">
                    <input type="checkbox" class="agent-tool-checkbox"
                        data-tool-id="${status.tool_id}"
                        ${isSelected ? 'checked' : ''}
                        onchange="onAgentToolCheckChange(this)"
                        aria-label="选择 ${status.tool_name}">
                </label>
                <span class="tool-icon">📦</span>
                <span class="tool-name">${status.tool_name}</span>
                <div style="margin-left:auto; display:flex; align-items:center; gap:0.5rem;">
                    ${statusBadge}
                    ${hasFile ? `<button class="btn-icon-small delete-btn" title="删除 ${status.tool_name} 的 AGENT.md"
                        onclick="event.stopPropagation(); handleDeleteToolAgent('${status.tool_id}', '${status.tool_name}')"
                        aria-label="删除 ${status.tool_name} 的 AGENT.md">
                        <svg width="13" height="13" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true">
                            <polyline points="1,3 11,3"/><path d="M2,3l.7,7.3a1,1,0,0,0,1,.7H8.3a1,1,0,0,0,1-.7L10,3"/>
                            <line x1="4.5" y1="5.5" x2="4.5" y2="9"/><line x1="7.5" y1="5.5" x2="7.5" y2="9"/>
                            <path d="M4,3V2a1,1,0,0,1,1-1H7a1,1,0,0,1,1,1V3"/>
                        </svg>
                    </button>` : ''}
                </div>
            </div>
            <div class="tool-path">${status.agent_path}</div>
            ${fileInfo}
        </div>`;
    }).join('');
}

/**
 * 渲染 Agent 库（右侧面板）
 */
function renderAgentLibrary() {
    const container = document.getElementById('agentLibraryContainer');
    if (!container) return;

    if (agentState.library.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无可用 Agent 文件</div>';
        return;
    }

    container.innerHTML = agentState.library.map(file => {
        const isSelected = agentState.selectedFiles.size > 0 && [...agentState.selectedFiles][0] === file.filename;
        return `
        <div class="card agent-file-card ${isSelected ? 'selected' : ''}"
            data-filename="${file.filename}"
            onclick="toggleAgentFile('${file.filename}')"
            role="radio" tabindex="0"
            aria-checked="${isSelected}"
            onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleAgentFile('${file.filename}')}">
            <div class="agent-file-name">${file.filename}</div>
            <div class="agent-file-size">${formatFileSize(file.size)}</div>
        </div>`;
    }).join('');
}

/**
 * 更新底部分发面板
 */
function updateAgentDistributionPanel() {
    // 目标工具显示
    const toolsDisplay = document.getElementById('agentTargetToolsDisplay');
    if (toolsDisplay) {
        if (agentState.selectedToolIds.size === 0) {
            toolsDisplay.innerHTML = '<span class="empty-hint">未选择工具</span>';
        } else {
            const names = Array.from(agentState.selectedToolIds).map(id => {
                const s = agentState.tools.find(t => t.tool_id === id);
                return s ? s.tool_name : id;
            });
            toolsDisplay.innerHTML = names.map(n =>
                `<span class="skill-tag">${n}</span>`
            ).join('');
        }
    }

    // 已选文件显示（单选，最多 1 个）
    const filesDisplay = document.getElementById('agentSelectedFiles');
    const countBadge = document.getElementById('agentSelectedCount');
    if (filesDisplay) {
        const selectedFile = agentState.selectedFile; // getter，取第一个
        if (!selectedFile) {
            filesDisplay.innerHTML = '<span class="empty-hint">未选择 Agent 文件</span>';
            if (countBadge) countBadge.textContent = '0';
        } else {
            filesDisplay.innerHTML = `<span class="skill-tag">${selectedFile}</span>`;
            if (countBadge) countBadge.textContent = '1';
        }
    }

    // 执行按钮状态
    const execBtn = document.getElementById('agentExecuteBtn');
    if (execBtn) {
        execBtn.disabled = agentState.selectedToolIds.size === 0 || agentState.selectedFiles.size === 0;
    }

    // 批量删除按钮
    const delBtn = document.getElementById('agentDeleteSelectedBtn');
    if (delBtn) {
        delBtn.style.display = agentState.selectedToolIds.size > 0 ? 'inline-flex' : 'none';
    }
}

// ==========================================
// Agent 页面交互
// ==========================================

/**
 * 切换 Agent 库文件选中（单选）
 */
function toggleAgentFile(filename) {
    // 单选：再次点击同一个则取消选中
    if (agentState.selectedFiles.has(filename)) {
        agentState.selectedFiles.clear();
    } else {
        agentState.selectedFiles.clear();
        agentState.selectedFiles.add(filename);
    }
    renderAgentLibrary();
    updateAgentDistributionPanel();
}
window.toggleAgentFile = toggleAgentFile;

/**
 * 点击工具卡片切换选中（多选）
 */
function toggleAgentTool(toolId) {
    if (agentState.selectedToolIds.has(toolId)) {
        agentState.selectedToolIds.delete(toolId);
    } else {
        agentState.selectedToolIds.add(toolId);
    }
    // 同步 checkbox 和卡片样式
    const card = document.querySelector(`.agent-tool-card[data-tool-id="${toolId}"]`);
    const checkbox = card && card.querySelector('.agent-tool-checkbox');
    const selected = agentState.selectedToolIds.has(toolId);
    if (card) {
        card.classList.toggle('selected', selected);
        card.setAttribute('aria-checked', selected);
    }
    if (checkbox) checkbox.checked = selected;
    updateAgentDistributionPanel();
}
window.toggleAgentTool = toggleAgentTool;

/**
 * 工具复选框变化时更新选中状态
 */
function onAgentToolCheckChange(checkbox) {
    const toolId = checkbox.dataset.toolId;
    if (checkbox.checked) {
        agentState.selectedToolIds.add(toolId);
    } else {
        agentState.selectedToolIds.delete(toolId);
    }
    // 同步卡片选中样式
    const card = document.querySelector(`.agent-tool-card[data-tool-id="${toolId}"]`);
    if (card) card.classList.toggle('selected', checkbox.checked);
    updateAgentDistributionPanel();
}
window.onAgentToolCheckChange = onAgentToolCheckChange;

/**
 * 执行 Agent 分发
 */
async function executeAgentDistribution() {
    if (agentState.selectedToolIds.size === 0 || !agentState.selectedFile) {
        showToast('请选择目标工具和 Agent 文件', 'warning');
        return;
    }

    const execBtn = document.getElementById('agentExecuteBtn');
    if (execBtn) execBtn.disabled = true;
    showToast('正在分发...', 'info');

    try {
        const response = await fetch('/api/agent/distribute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tool_ids: Array.from(agentState.selectedToolIds),
                agent_filename: agentState.selectedFile,
                distribute_method: agentState.distributeMethod,
            }),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || '分发请求失败');

        const type = result.success ? 'success' : 'warning';
        showToast(result.message, type);

        // 刷新工具状态，并重置所有选中状态
        agentState.selectedToolIds.clear();
        agentState.selectedFiles.clear();
        await loadAgentPageData();
        updateAgentDistributionPanel();
    } catch (error) {
        console.error('executeAgentDistribution error:', error);
        showToast(`分发失败: ${error.message}`, 'error');
    } finally {
        if (execBtn) execBtn.disabled = false;
    }
}
window.executeAgentDistribution = executeAgentDistribution;

/**
 * 删除单个工具的 AGENT.md
 */
async function handleDeleteToolAgent(toolId, toolName) {
    if (!confirm(`确认删除「${toolName}」的 AGENT.md？\n软链接仅删除链接本身，源文件不受影响。`)) return;

    try {
        const response = await fetch(`/api/tools/${toolId}/agent`, { method: 'DELETE' });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || '删除失败');

        showToast(`已删除 ${toolName} 的 AGENT.md`, 'success');
        // 刷新该工具状态
        const newStatus = await fetchToolAgentStatus(toolId);
        if (newStatus) {
            const idx = agentState.tools.findIndex(t => t.tool_id === toolId);
            if (idx !== -1) agentState.tools[idx] = newStatus;
        }
        agentState.selectedToolIds.delete(toolId);
        renderAgentTools();
        updateAgentDistributionPanel();
    } catch (error) {
        console.error('handleDeleteToolAgent error:', error);
        showToast(`删除失败: ${error.message}`, 'error');
    }
}
window.handleDeleteToolAgent = handleDeleteToolAgent;

/**
 * 批量删除选中工具的 AGENT.md
 */
async function handleBatchDeleteAgentTools() {
    if (agentState.selectedToolIds.size === 0) return;

    const names = Array.from(agentState.selectedToolIds).map(id => {
        const s = agentState.tools.find(t => t.tool_id === id);
        return s ? s.tool_name : id;
    });

    if (!confirm(`确认删除以下 ${names.length} 个工具的 AGENT.md？\n${names.join('、')}`)) return;

    let successCount = 0;
    let failCount = 0;

    for (const toolId of agentState.selectedToolIds) {
        try {
            const response = await fetch(`/api/tools/${toolId}/agent`, { method: 'DELETE' });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || '删除失败');
            }
            successCount++;
        } catch (error) {
            console.error(`删除 ${toolId} Agent 失败:`, error);
            failCount++;
        }
    }

    showToast(
        failCount === 0
            ? `已删除 ${successCount} 个工具的 AGENT.md`
            : `删除完成: 成功 ${successCount}，失败 ${failCount}`,
        failCount === 0 ? 'success' : 'warning'
    );

    agentState.selectedToolIds.clear();
    await loadAgentPageData();
}
window.handleBatchDeleteAgentTools = handleBatchDeleteAgentTools;

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

// ==========================================
// Agent 页面事件绑定（在 bindEvents 中调用）
// ==========================================

function bindAgentEvents() {
    // Agent 页面"添加工具"按钮：复用 Skills 页面的 addToolModal
    const agentAddToolBtn = document.getElementById('agentAddToolBtn');
    if (agentAddToolBtn) {
        agentAddToolBtn.addEventListener('click', () => {
            document.getElementById('addToolModal').classList.add('show');
        });
    }

    // 分发方式按钮
    document.querySelectorAll('#agentDistributionMethods .method-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#agentDistributionMethods .method-btn').forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-pressed', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-pressed', 'true');
            agentState.distributeMethod = btn.dataset.method;
        });
    });

    // 执行分发按钮
    const execBtn = document.getElementById('agentExecuteBtn');
    if (execBtn) execBtn.addEventListener('click', executeAgentDistribution);

    // 取消按钮
    const cancelBtn = document.getElementById('agentCancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            agentState.selectedToolIds.clear();
            agentState.selectedFiles.clear();
            renderAgentTools();
            renderAgentLibrary();
            updateAgentDistributionPanel();
            showToast('已重置选择', 'info');
        });
    }

    // 批量删除按钮
    const batchDelBtn = document.getElementById('agentDeleteSelectedBtn');
    if (batchDelBtn) batchDelBtn.addEventListener('click', handleBatchDeleteAgentTools);
}
