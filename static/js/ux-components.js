/**
 * 统一用户体验组件
 * 提供：Toast提示、加载状态、表单验证、操作反馈等功能
 */

// ============================================================================
// 1. Toast 提示系统（替代 alert）
// ============================================================================

/**
 * 显示 Toast 提示
 * @param {string} message - 提示消息
 * @param {string} type - 类型：'success', 'error', 'warning', 'info'
 * @param {number} duration - 显示时长（毫秒），默认 3000
 */
function showToast(message, type = 'info', duration = 3000) {
    // 确保 Toast 容器存在
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        toastContainer.setAttribute('aria-live', 'polite');
        toastContainer.setAttribute('aria-atomic', 'true');
        document.body.appendChild(toastContainer);
    }

    // 创建 Toast 元素
    const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.setAttribute('data-bs-autohide', 'true');
    toast.setAttribute('data-bs-delay', duration);

    // 根据类型设置样式
    const typeConfig = {
        'success': { bg: 'bg-success', icon: 'fa-check-circle', title: '成功' },
        'error': { bg: 'bg-danger', icon: 'fa-exclamation-circle', title: '错误' },
        'warning': { bg: 'bg-warning', icon: 'fa-exclamation-triangle', title: '警告' },
        'info': { bg: 'bg-info', icon: 'fa-info-circle', title: '提示' }
    };

    const config = typeConfig[type] || typeConfig['info'];

    toast.innerHTML = `
        <div class="toast-header ${config.bg} text-white">
            <i class="fas ${config.icon} me-2"></i>
            <strong class="me-auto">${config.title}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;

    toastContainer.appendChild(toast);

    // 初始化并显示 Toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Toast 隐藏后移除元素
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });

    return bsToast;
}

// 便捷方法
const Toast = {
    success: (message, duration) => showToast(message, 'success', duration),
    error: (message, duration) => showToast(message, 'error', duration || 5000),
    warning: (message, duration) => showToast(message, 'warning', duration),
    info: (message, duration) => showToast(message, 'info', duration)
};

// ============================================================================
// 2. 统一加载状态组件
// ============================================================================

/**
 * 显示加载状态
 * @param {string|HTMLElement} target - 目标元素选择器或元素
 * @param {string} message - 加载提示文字
 * @param {string} size - 大小：'sm', 'md', 'lg'
 */
function showLoading(target, message = '加载中...', size = 'md') {
    const element = typeof target === 'string' ? document.querySelector(target) : target;
    if (!element) return null;

    // 保存原始内容
    if (!element.dataset.originalContent) {
        element.dataset.originalContent = element.innerHTML;
    }

    const sizeClass = size === 'sm' ? 'spinner-border-sm' : size === 'lg' ? '' : '';
    element.innerHTML = `
        <div class="d-flex align-items-center justify-content-center" style="min-height: 100px;">
            <div class="spinner-border ${sizeClass} text-primary me-3" role="status">
                <span class="visually-hidden">${message}</span>
            </div>
            <span class="text-muted">${message}</span>
        </div>
    `;
    element.style.pointerEvents = 'none';
    element.style.opacity = '0.6';

    return {
        hide: () => hideLoading(target)
    };
}

/**
 * 隐藏加载状态
 * @param {string|HTMLElement} target - 目标元素选择器或元素
 */
function hideLoading(target) {
    const element = typeof target === 'string' ? document.querySelector(target) : target;
    if (!element) return;

    if (element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    }
    element.style.pointerEvents = '';
    element.style.opacity = '';
}

/**
 * 显示全屏加载遮罩
 * @param {string} message - 加载提示文字
 */
function showFullScreenLoading(message = '加载中...') {
    let overlay = document.getElementById('fullscreen-loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'fullscreen-loading-overlay';
        overlay.className = 'fullscreen-loading-overlay';
        document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
        <div class="fullscreen-loading-content">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">${message}</span>
            </div>
            <div class="text-white">${message}</div>
        </div>
    `;
    overlay.style.display = 'flex';
}

/**
 * 隐藏全屏加载遮罩
 */
function hideFullScreenLoading() {
    const overlay = document.getElementById('fullscreen-loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// ============================================================================
// 3. 表单验证增强
// ============================================================================

/**
 * 实时表单验证
 * @param {HTMLFormElement} form - 表单元素
 * @param {Object} rules - 验证规则
 */
function initFormValidation(form, rules = {}) {
    if (!form) return;

    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        // 实时验证
        input.addEventListener('blur', function() {
            validateField(this, rules[this.name] || {});
        });

        // 清除错误状态
        input.addEventListener('input', function() {
            clearFieldError(this);
        });
    });

    // 表单提交验证
    form.addEventListener('submit', function(e) {
        if (!validateForm(form, rules)) {
            e.preventDefault();
            return false;
        }
    });
}

/**
 * 验证单个字段
 * @param {HTMLElement} field - 字段元素
 * @param {Object} rule - 验证规则
 */
function validateField(field, rule = {}) {
    const value = field.value.trim();
    let error = null;

    // 必填验证
    if (rule.required && !value) {
        error = rule.requiredMessage || `${field.placeholder || field.name}不能为空`;
    }
    // 最小长度
    else if (rule.minLength && value.length < rule.minLength) {
        error = rule.minLengthMessage || `至少需要${rule.minLength}个字符`;
    }
    // 最大长度
    else if (rule.maxLength && value.length > rule.maxLength) {
        error = rule.maxLengthMessage || `最多${rule.maxLength}个字符`;
    }
    // 正则验证
    else if (rule.pattern && !rule.pattern.test(value)) {
        error = rule.patternMessage || '格式不正确';
    }
    // 自定义验证
    else if (rule.validator && typeof rule.validator === 'function') {
        const result = rule.validator(value);
        if (result !== true) {
            error = result || '验证失败';
        }
    }

    if (error) {
        showFieldError(field, error);
        return false;
    } else {
        clearFieldError(field);
        return true;
    }
}

/**
 * 显示字段错误
 * @param {HTMLElement} field - 字段元素
 * @param {string} message - 错误消息
 */
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * 清除字段错误
 * @param {HTMLElement} field - 字段元素
 */
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * 验证整个表单
 * @param {HTMLFormElement} form - 表单元素
 * @param {Object} rules - 验证规则
 */
function validateForm(form, rules = {}) {
    const inputs = form.querySelectorAll('input, textarea, select');
    let isValid = true;

    inputs.forEach(input => {
        if (!validateField(input, rules[input.name] || {})) {
            isValid = false;
        }
    });

    return isValid;
}

// ============================================================================
// 4. 操作反馈和防重复提交
// ============================================================================

/**
 * 防重复提交的按钮处理
 * @param {HTMLElement|string} button - 按钮元素或选择器
 * @param {Function} callback - 点击回调函数
 * @param {Object} options - 选项
 */
function preventDoubleSubmit(button, callback, options = {}) {
    const btn = typeof button === 'string' ? document.querySelector(button) : button;
    if (!btn) return;

    const {
        loadingText = '处理中...',
        disabledClass = 'disabled',
        showLoading = true
    } = options;

    btn.addEventListener('click', async function(e) {
        // 如果已经在处理中，阻止提交
        if (btn.dataset.processing === 'true') {
            e.preventDefault();
            return false;
        }

        // 标记为处理中
        btn.dataset.processing = 'true';
        const originalText = btn.innerHTML;
        const originalDisabled = btn.disabled;

        // 更新按钮状态
        btn.disabled = true;
        if (showLoading) {
            btn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                ${loadingText}
            `;
        }
        btn.classList.add(disabledClass);

        try {
            // 执行回调
            if (callback && typeof callback === 'function') {
                await callback(e);
            }
        } catch (error) {
            console.error('操作失败:', error);
            Toast.error(error.message || '操作失败，请重试');
        } finally {
            // 恢复按钮状态
            setTimeout(() => {
                btn.dataset.processing = 'false';
                btn.disabled = originalDisabled;
                btn.innerHTML = originalText;
                btn.classList.remove(disabledClass);
            }, 500); // 延迟500ms恢复，避免闪烁
        }
    });
}

/**
 * 处理 API 响应并显示反馈
 * @param {Response} response - Fetch API 响应
 * @param {Object} options - 选项
 */
async function handleApiResponse(response, options = {}) {
    const {
        showSuccessToast = true,
        showErrorToast = true,
        successMessage = '操作成功',
        onSuccess = null,
        onError = null
    } = options;

    try {
        const data = await response.json();
        
        if (response.ok && (data.success !== false && data.status !== 'error')) {
            if (showSuccessToast) {
                Toast.success(data.message || successMessage);
            }
            if (onSuccess && typeof onSuccess === 'function') {
                onSuccess(data);
            }
            return { success: true, data };
        } else {
            const errorMsg = data.message || data.error || '操作失败';
            if (showErrorToast) {
                Toast.error(errorMsg);
            }
            if (onError && typeof onError === 'function') {
                onError(data);
            }
            return { success: false, data, error: errorMsg };
        }
    } catch (error) {
        const errorMsg = '网络错误，请检查网络连接';
        if (showErrorToast) {
            Toast.error(errorMsg);
        }
        if (onError && typeof onError === 'function') {
            onError({ error: errorMsg });
        }
        return { success: false, error: errorMsg };
    }
}

// ============================================================================
// 5. 导出到全局
// ============================================================================

// 将工具函数挂载到 window 对象，方便全局使用
if (typeof window !== 'undefined') {
    window.UX = {
        Toast,
        showToast,
        showLoading,
        hideLoading,
        showFullScreenLoading,
        hideFullScreenLoading,
        initFormValidation,
        validateField,
        validateForm,
        showFieldError,
        clearFieldError,
        preventDoubleSubmit,
        handleApiResponse
    };

    // 兼容性：用 Toast 替代 alert，不再打 console.warn 避免控制台刷屏
    const originalAlert = window.alert;
    window.alert = function(message) {
        Toast.info(message);
    };
}
