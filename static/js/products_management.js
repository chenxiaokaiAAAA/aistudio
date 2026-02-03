/**
 * 产品管理页面JavaScript
 * 处理三栏布局的交互逻辑
 */

// 全局变量
let selectedCategoryId = null;
let selectedSubcategoryId = null;
// subcategoriesByCategory 将在页面中定义

// 选择一级分类
function selectCategory(categoryId) {
    selectedCategoryId = categoryId;
    selectedSubcategoryId = null;
    
    // 更新一级分类选中状态
    document.querySelectorAll('.category-list-item').forEach(item => {
        item.classList.remove('active');
    });
    const categoryItem = document.querySelector(`[data-category-id="${categoryId}"]`);
    if (categoryItem) {
        categoryItem.classList.add('active');
    }
    
    // 更新二级分类列表
    loadSubcategories(categoryId);
    
    // 更新产品列表
    filterProducts();
    
    // 显示添加二级分类按钮
    const addSubcategoryBtn = document.getElementById('addSubcategoryBtn');
    if (addSubcategoryBtn) {
        addSubcategoryBtn.style.display = 'block';
    }
}

// 加载二级分类
function loadSubcategories(categoryId) {
    const subcategoryList = document.getElementById('subcategoryList');
    if (!subcategoryList) return;
    
    const subcategories = subcategoriesByCategory[categoryId] || [];
    
    // 更新标题
    const categoryName = document.querySelector(`[data-category-id="${categoryId}"]`)?.textContent.trim() || '二级分类';
    const currentCategoryName = document.getElementById('currentCategoryName');
    if (currentCategoryName) {
        currentCategoryName.textContent = categoryName;
    }
    
    const subcategoryCount = document.getElementById('subcategoryCount');
    if (subcategoryCount) {
        subcategoryCount.textContent = `(${subcategories.length})`;
    }
    
    if (subcategories.length === 0) {
        subcategoryList.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-folder-open fa-2x mb-2"></i>
                <p>该分类下暂无二级分类</p>
                <button class="btn btn-sm btn-success" onclick="openAddSubcategoryModal()">
                    <i class="fas fa-plus"></i> 添加二级分类
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    // 按sort_order排序
    subcategories.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
    
    subcategories.forEach(sub => {
        html += `
            <div class="subcategory-list-item" data-subcategory-id="${sub.id}" onclick="selectSubcategory(${sub.id})">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${sub.icon ? sub.icon + ' ' : ''}${sub.name}</strong>
                        <small class="text-muted d-block">${sub.code}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-light" onclick="event.stopPropagation(); editSubcategory(${sub.id}, ${categoryId})">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    subcategoryList.innerHTML = html;
    
    // 显示排序按钮（如果有二级分类）
    const sortBtn = document.getElementById('sortSubcategoryBtn');
    if (sortBtn) {
        sortBtn.style.display = subcategories.length > 0 ? 'inline-block' : 'none';
    }
}

// 选择二级分类
function selectSubcategory(subcategoryId) {
    selectedSubcategoryId = subcategoryId;
    
    // 更新二级分类选中状态
    document.querySelectorAll('.subcategory-list-item').forEach(item => {
        item.classList.remove('active');
    });
    const clickedItem = event.target.closest('.subcategory-list-item');
    if (clickedItem) {
        clickedItem.classList.add('active');
    }
    
    // 更新产品列表
    filterProducts();
}

// 过滤产品
function filterProducts() {
    const productItems = document.querySelectorAll('.product-card-item');
    let visibleCount = 0;
    
    productItems.forEach(item => {
        const productCategoryId = item.dataset.categoryId || '';
        const productSubcategoryId = item.dataset.subcategoryId || '';
        
        let shouldShow = true;
        
        if (selectedCategoryId) {
            if (productCategoryId != selectedCategoryId) {
                shouldShow = false;
            }
            
            if (selectedSubcategoryId !== null) {
                if (productSubcategoryId != selectedSubcategoryId) {
                    shouldShow = false;
                }
            }
        }
        
        if (shouldShow) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });
    
    // 更新产品计数
    const productCount = document.getElementById('productCount');
    if (productCount) {
        productCount.textContent = `(${visibleCount})`;
    }
    
    // 更新产品标题
    let title = '产品列表';
    if (selectedCategoryId) {
        const categoryName = document.querySelector(`[data-category-id="${selectedCategoryId}"]`)?.textContent.trim() || '';
        title = categoryName;
        if (selectedSubcategoryId !== null) {
            const subcategoryName = document.querySelector(`[onclick="selectSubcategory(${selectedSubcategoryId})"]`)?.textContent.trim() || '';
            title += ' - ' + subcategoryName;
        }
    }
    const currentProductTitle = document.getElementById('currentProductTitle');
    if (currentProductTitle) {
        currentProductTitle.textContent = title;
    }
}

// 打开添加一级分类模态框
function openAddCategoryModal() {
    // 重置表单
    const form = document.getElementById('categoryForm');
    if (form) {
        form.reset();
    }
    
    // 清空隐藏字段
    document.getElementById('categoryId').value = '';
    document.getElementById('categoryImageUrl').value = '';
    
    // 清空跳转页面字段
    const styleRedirectPageElement = document.getElementById('categoryStyleRedirectPage');
    if (styleRedirectPageElement) {
        styleRedirectPageElement.value = '';
    }
    
    // 重置图片预览
    const preview = document.getElementById('categoryImagePreview');
    const uploadArea = document.getElementById('categoryImageUploadArea');
    if (preview) {
        preview.style.display = 'none';
    }
    if (uploadArea) {
        uploadArea.style.display = 'block';
    }
    
    // 更新模态框标题
    document.getElementById('categoryModalTitle').textContent = '添加一级分类';
    
    // 显示模态框
    const modalElement = document.getElementById('addCategoryModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

// 打开添加产品模态框（自动填充分类）
function openAddProductModal() {
    const form = document.getElementById('productForm');
    if (form) {
        form.reset();
    }
    
    // 自动填充分类
    const categorySelect = document.getElementById('add_category_select');
    const subcategorySelect = document.getElementById('add_subcategory_select');
    
    if (selectedCategoryId && categorySelect) {
        categorySelect.value = selectedCategoryId;
        updateAddSubcategories();
    }
    if (selectedSubcategoryId !== null && subcategorySelect) {
        subcategorySelect.value = selectedSubcategoryId;
    }
}

// 更新添加产品表单的二级分类选项
function updateAddSubcategories() {
    const categorySelect = document.getElementById('add_category_select');
    const subcategorySelect = document.getElementById('add_subcategory_select');
    
    if (!categorySelect || !subcategorySelect) return;
    
    const selectedCategoryId = categorySelect.value;
    
    // 清空二级分类选项
    subcategorySelect.innerHTML = '<option value="">-- 请选择二级分类 --</option>';
    
    // 如果有选择一级分类，添加对应的二级分类选项
    if (selectedCategoryId) {
        const categoryId = parseInt(selectedCategoryId);
        const subcategories = subcategoriesByCategory[categoryId] || [];
        
        subcategories.forEach(subcat => {
            const option = document.createElement('option');
            option.value = subcat.id;
            const displayText = (subcat.icon ? subcat.icon + ' ' : '') + subcat.name;
            option.textContent = displayText;
            subcategorySelect.appendChild(option);
        });
    }
}

// 打开添加二级分类模态框
function openAddSubcategoryModal() {
    if (!selectedCategoryId) {
        alert('请先选择一级分类');
        return;
    }
    
    const modal = document.getElementById('addSubcategoryModal');
    const form = document.getElementById('subcategoryForm');
    if (form) {
        form.reset();
        document.getElementById('subcategoryId').value = '';
        document.getElementById('subcategoryCategoryId').value = selectedCategoryId;
        document.getElementById('subcategoryModalTitle').textContent = '添加二级分类';
    }
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// 上传分类图片
async function uploadCategoryImage(input) {
    const file = input.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/api/admin/product-categories/upload-image', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            const imageUrl = result.data.image_url;
            document.getElementById('categoryImageUrl').value = imageUrl;
            
            // 显示预览
            const preview = document.getElementById('categoryImagePreview');
            const uploadArea = document.getElementById('categoryImageUploadArea');
            if (preview) {
                preview.src = imageUrl;
                preview.style.display = 'block';
            }
            if (uploadArea) {
                uploadArea.style.display = 'none';
            }
        } else {
            alert('图片上传失败：' + result.message);
        }
    } catch (error) {
        console.error('上传图片失败:', error);
        alert('图片上传失败，请重试');
    }
}

// 保存一级分类
async function saveCategory() {
    const form = document.getElementById('categoryForm');
    const categoryId = document.getElementById('categoryId').value;
    
    // 获取跳转页面字段的值
    const styleRedirectPageElement = document.getElementById('categoryStyleRedirectPage');
    let styleRedirectPageValue = null;
    if (styleRedirectPageElement) {
        const rawValue = styleRedirectPageElement.value.trim();
        styleRedirectPageValue = rawValue ? rawValue : null;
        console.log('✅ 找到 categoryStyleRedirectPage 元素，值:', styleRedirectPageValue);
    } else {
        console.warn('⚠️ 找不到 categoryStyleRedirectPage 元素');
        styleRedirectPageValue = null;
    }
    
    const data = {
        name: document.getElementById('categoryName').value,
        code: document.getElementById('categoryCode').value,
        icon: document.getElementById('categoryIcon').value,
        image_url: document.getElementById('categoryImageUrl').value || '',
        sort_order: parseInt(document.getElementById('categorySortOrder').value) || 0,
        is_active: document.getElementById('categoryIsActive').checked,
        style_redirect_page: styleRedirectPageValue  // 添加跳转页面字段
    };
    
    console.log('📤 保存分类数据:', { ...data, style_redirect_page: styleRedirectPageValue });

    try {
        const url = categoryId 
            ? `/api/admin/product-categories/${categoryId}`
            : '/api/admin/product-categories';
        const method = categoryId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.status === 'success') {
            alert(result.message);
            bootstrap.Modal.getInstance(document.getElementById('addCategoryModal')).hide();
            location.reload();
        } else {
            alert('操作失败：' + result.message);
        }
    } catch (error) {
        console.error('保存分类失败:', error);
        alert('保存失败，请重试');
    }
}

// 保存二级分类
async function saveSubcategory() {
    const form = document.getElementById('subcategoryForm');
    const subcategoryId = document.getElementById('subcategoryId').value;
    const categoryId = document.getElementById('subcategoryCategoryId').value;
    
    const data = {
        category_id: parseInt(categoryId),
        name: document.getElementById('subcategoryName').value,
        code: document.getElementById('subcategoryCode').value,
        icon: document.getElementById('subcategoryIcon').value,
        sort_order: parseInt(document.getElementById('subcategorySortOrder').value) || 0,
        is_active: document.getElementById('subcategoryIsActive').checked
    };

    try {
        const url = subcategoryId 
            ? `/api/admin/product-subcategories/${subcategoryId}`
            : '/api/admin/product-subcategories';
        const method = subcategoryId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.status === 'success') {
            alert(result.message);
            bootstrap.Modal.getInstance(document.getElementById('addSubcategoryModal')).hide();
            location.reload();
        } else {
            alert('操作失败：' + result.message);
        }
    } catch (error) {
        console.error('保存二级分类失败:', error);
        alert('保存失败，请重试');
    }
}

// 编辑一级分类
// 编辑一级分类 - 打开编辑模态框
async function editCategory(categoryId) {
    console.log('编辑一级分类，ID:', categoryId);
    
    try {
        // 获取分类详情
        const response = await fetch(`/api/admin/product-categories/${categoryId}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const category = result.data;
            
            // 填充表单
            document.getElementById('categoryId').value = category.id || '';
            document.getElementById('categoryName').value = category.name || '';
            document.getElementById('categoryCode').value = category.code || '';
            document.getElementById('categoryIcon').value = category.icon || '';
            document.getElementById('categorySortOrder').value = category.sort_order || 0;
            document.getElementById('categoryIsActive').checked = category.is_active !== false;
            document.getElementById('categoryImageUrl').value = category.image_url || '';
            
            // 设置跳转页面字段
            const styleRedirectPageElement = document.getElementById('categoryStyleRedirectPage');
            if (styleRedirectPageElement) {
                styleRedirectPageElement.value = category.style_redirect_page || '';
                console.log('✅ 设置 categoryStyleRedirectPage 值为:', category.style_redirect_page || '');
            } else {
                console.warn('⚠️ 找不到 categoryStyleRedirectPage 元素');
            }
            
            // 更新模态框标题
            document.getElementById('categoryModalTitle').textContent = '编辑一级分类';
            
            // 显示图片预览
            const preview = document.getElementById('categoryImagePreview');
            const uploadArea = document.getElementById('categoryImageUploadArea');
            if (category.image_url) {
                if (preview) {
                    preview.src = category.image_url;
                    preview.style.display = 'block';
                }
                if (uploadArea) {
                    uploadArea.style.display = 'none';
                }
            } else {
                if (preview) {
                    preview.style.display = 'none';
                }
                if (uploadArea) {
                    uploadArea.style.display = 'block';
                }
            }
            
            // 显示模态框
            const modalElement = document.getElementById('addCategoryModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        } else {
            alert('获取分类信息失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('编辑分类失败:', error);
        alert('编辑分类失败: ' + error.message);
    }
}

// 编辑二级分类
async function editSubcategory(subcategoryId, categoryId) {
    console.log('编辑二级分类，ID:', subcategoryId, '一级分类ID:', categoryId);
    
    try {
        // 获取二级分类详情
        const response = await fetch(`/api/admin/product-categories/subcategories/${subcategoryId}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const subcategory = result.data;
            
            // 填充表单
            document.getElementById('subcategoryId').value = subcategory.id || '';
            document.getElementById('subcategoryCategoryId').value = categoryId || subcategory.category_id || '';
            document.getElementById('subcategoryName').value = subcategory.name || '';
            document.getElementById('subcategoryCode').value = subcategory.code || '';
            document.getElementById('subcategoryIcon').value = subcategory.icon || '';
            document.getElementById('subcategorySortOrder').value = subcategory.sort_order || 0;
            document.getElementById('subcategoryIsActive').checked = subcategory.is_active !== false;
            
            // 更新模态框标题
            document.getElementById('subcategoryModalTitle').textContent = '编辑二级分类';
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('addSubcategoryModal'));
            modal.show();
        } else {
            alert('获取二级分类信息失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('编辑二级分类失败:', error);
        alert('编辑二级分类失败: ' + error.message);
    }
}

// 编辑产品
// 编辑产品 - 打开编辑模态框
async function editProduct(productId) {
    console.log('编辑产品，ID:', productId);
    
    try {
        // 获取产品详情
        const response = await fetch(`/api/admin/products/${productId}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const product = result.data;
            
            // 先显示模态框，确保 DOM 元素已加载
            const modalElement = document.getElementById('addProductModal');
            if (!modalElement) {
                alert('找不到产品编辑模态框，请刷新页面重试');
                return;
            }
            
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // 等待模态框完全显示后再填充数据
            setTimeout(() => {
                // 填充编辑表单
                const productIdEl = document.getElementById('productId');
                const productCodeEl = document.getElementById('productCode');
                const productNameEl = document.getElementById('productName');
                const productDescriptionEl = document.getElementById('productDescription');
                const productSortOrderEl = document.getElementById('productSortOrder');
                const productFreeSelectionCountEl = document.getElementById('productFreeSelectionCount');
                const productExtraPhotoPriceEl = document.getElementById('productExtraPhotoPrice');
                const productIsActiveEl = document.getElementById('productIsActive');
                
                if (productIdEl) productIdEl.value = product.id;
                if (productCodeEl) productCodeEl.value = product.code || '';
                if (productNameEl) productNameEl.value = product.name || '';
                if (productDescriptionEl) productDescriptionEl.value = product.description || '';
                if (productSortOrderEl) productSortOrderEl.value = product.sort_order || 0;
                if (productFreeSelectionCountEl) productFreeSelectionCountEl.value = product.free_selection_count || 1;
                if (productExtraPhotoPriceEl) productExtraPhotoPriceEl.value = product.extra_photo_price || 10.0;
                if (productIsActiveEl) productIsActiveEl.checked = product.is_active !== false;
            
                // 设置分类
                if (product.category_id) {
                    const categorySelect = document.getElementById('add_category_select');
                    if (categorySelect) {
                        categorySelect.value = product.category_id;
                        updateAddSubcategories();
                        if (product.subcategory_id) {
                            setTimeout(() => {
                                const subcategorySelect = document.getElementById('add_subcategory_select');
                                if (subcategorySelect) {
                                    subcategorySelect.value = product.subcategory_id;
                                }
                            }, 100);
                        }
                    }
                }
                
                // 显示主图预览
                const mainImagePreview = document.getElementById('editMainImagePreview');
                if (mainImagePreview) {
                    if (product.image_url) {
                        mainImagePreview.innerHTML = `<img src="${product.image_url}" style="max-width: 200px; max-height: 200px; border-radius: 8px;" alt="主图">`;
                    } else {
                        mainImagePreview.innerHTML = '<p class="text-muted">暂无主图</p>';
                    }
                }
                
                // 显示多图预览
                const imagesPreview = document.getElementById('editImagesPreview');
                if (imagesPreview) {
                    if (product.images && product.images.length > 0) {
                        imagesPreview.innerHTML = product.images.map(img => 
                            `<img src="${img.image_url}" style="max-width: 100px; max-height: 100px; border-radius: 4px; margin-right: 5px; margin-bottom: 5px;" alt="产品图">`
                        ).join('');
                    } else {
                        imagesPreview.innerHTML = '<p class="text-muted">暂无图片</p>';
                    }
                }
                
                // 加载尺寸数据
                loadProductSizesForEdit(product.sizes || []);
                
                // 加载自定义字段
                loadProductCustomFieldsForEdit(product.custom_fields || []);
                
                // 加载风格绑定（API返回的是style_category_ids数组）
                loadProductStyleBindingsForEdit(product.style_category_ids || []);
                
                // 更新模态框标题和表单 action
                const modalTitle = modalElement.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = '编辑产品';
                }
                const actionInput = document.getElementById('productForm')?.querySelector('input[name="action"]');
                if (actionInput) {
                    actionInput.value = 'edit_product';
                }
            }, 100); // 等待模态框动画完成
        } else {
            alert('获取产品信息失败：' + result.message);
        }
    } catch (error) {
        console.error('编辑产品失败:', error);
        alert('编辑产品失败，请重试');
    }
}

// 在模态框中添加尺寸
function addSizeInModal() {
    const container = document.getElementById('sizesContainer');
    if (!container) return;
    
    const newSizeItem = document.createElement('div');
    newSizeItem.className = 'size-input-group border rounded p-3 mb-3';
    newSizeItem.innerHTML = `
        <input type="hidden" name="existing_size_id[]" value="">
        <div class="row">
            <div class="col-md-3">
                <label class="form-label small">尺寸名称 <span class="text-danger">*</span></label>
                <input type="text" class="form-control" name="size_name[]" required>
            </div>
            <div class="col-md-2">
                <label class="form-label small">价格 <span class="text-danger">*</span></label>
                <input type="number" step="0.01" class="form-control" name="size_price[]" required>
            </div>
            <div class="col-md-2">
                <label class="form-label small">厂家ID</label>
                <input type="text" class="form-control" name="size_printer_id[]">
            </div>
            <div class="col-md-3">
                <label class="form-label small">效果图（小程序展示）</label>
                <input type="file" class="form-control form-control-sm" name="size_effect_image[]" accept="image/*" onchange="handleSizeEffectImageChange(this)">
                <input type="hidden" name="size_effect_image_url[]" value="">
                <div class="size-effect-image-preview mt-1"></div>
            </div>
            <div class="col-md-2">
                <label class="form-label small">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger btn-sm w-100" onclick="removeSizeInModal(this)">删除</button>
            </div>
        </div>
    `;
    container.appendChild(newSizeItem);
}

// 处理尺寸效果图上传
function handleSizeEffectImageChange(input) {
    const file = input.files[0];
    if (!file) return;
    
    const preview = input.closest('.row').querySelector('.size-effect-image-preview');
    const hiddenInput = input.closest('.row').querySelector('input[name="size_effect_image_url[]"]');
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = function(e) {
        if (preview) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 60px; max-height: 60px; border-radius: 4px; border: 1px solid #ddd;">`;
        }
    };
    reader.readAsDataURL(file);
}

// 在模态框中删除尺寸
function removeSizeInModal(button) {
    button.closest('.size-input-group').remove();
}

// 加载产品尺寸数据到编辑表单
function loadProductSizesForEdit(sizes) {
    const container = document.getElementById('sizesContainer');
    if (!container) return;
    
    // 清空现有尺寸
    container.innerHTML = '';
    
    // 添加尺寸
    sizes.forEach(size => {
        const sizeItem = document.createElement('div');
        sizeItem.className = 'size-input-group border rounded p-3 mb-3';
        const effectImageUrl = size.effect_image_url || '';
        const effectImagePreview = effectImageUrl 
            ? `<img src="${effectImageUrl}" style="max-width: 60px; max-height: 60px; border-radius: 4px; border: 1px solid #ddd;">`
            : '<small class="text-muted">未上传图片</small>';
        
        sizeItem.innerHTML = `
            <input type="hidden" name="existing_size_id[]" value="${size.id}">
            <div class="row">
                <div class="col-md-3">
                    <label class="form-label small">尺寸名称 <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" name="size_name[]" value="${size.size_name || ''}" required>
                </div>
                <div class="col-md-2">
                    <label class="form-label small">价格 <span class="text-danger">*</span></label>
                    <input type="number" step="0.01" class="form-control" name="size_price[]" value="${size.price || ''}" required>
                </div>
                <div class="col-md-2">
                    <label class="form-label small">厂家ID</label>
                    <input type="text" class="form-control" name="size_printer_id[]" value="${size.printer_id || ''}">
                </div>
                <div class="col-md-3">
                    <label class="form-label small">效果图（小程序展示）</label>
                    <input type="file" class="form-control form-control-sm" name="size_effect_image[]" accept="image/*" onchange="handleSizeEffectImageChange(this)">
                    <input type="hidden" name="size_effect_image_url[]" value="${effectImageUrl}">
                    <div class="size-effect-image-preview mt-1">${effectImagePreview}</div>
                </div>
                <div class="col-md-2">
                    <label class="form-label small">&nbsp;</label>
                    <button type="button" class="btn btn-outline-danger btn-sm w-100" onclick="removeSizeInModal(this)">删除</button>
                </div>
            </div>
        `;
        container.appendChild(sizeItem);
    });
    
    // 如果没有尺寸，至少添加一个空尺寸
    if (sizes.length === 0) {
        addSizeInModal();
    }
}

// 加载产品自定义字段到编辑表单（已在上面实现）

// 加载产品风格绑定到编辑表单
function loadProductStyleBindingsForEdit(styleBindings) {
    // 清除所有复选框
    document.querySelectorAll('input[name="style_category_ids[]"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    console.log('🔍 加载风格分类绑定:', styleBindings);
    
    // 选中已绑定的风格分类
    // styleBindings 现在是一个ID数组，而不是对象数组
    if (Array.isArray(styleBindings)) {
        styleBindings.forEach(categoryId => {
            const checkbox = document.getElementById(`style_cat_new_${categoryId}`);
            if (checkbox) {
                checkbox.checked = true;
                console.log(`✅ 选中风格分类复选框: ID=${categoryId}`);
            } else {
                console.warn(`⚠️ 未找到风格分类复选框: ID=${categoryId}, 选择器: style_cat_new_${categoryId}`);
            }
        });
    } else {
        console.warn('⚠️ styleBindings不是数组:', styleBindings);
    }
}

// 提交产品表单（在提交前更新自定义字段的JSON）
function submitProductForm() {
    const form = document.getElementById('productForm');
    if (!form) {
        alert('找不到表单');
        return;
    }
    
    // 更新所有自定义字段的选项JSON
    const allFieldItems = form.querySelectorAll('.custom-field-item');
    allFieldItems.forEach((fieldItem) => {
        const optionsList = fieldItem.querySelector('.options-list');
        if (optionsList) {
            updateFieldOptionsJSONInModal(optionsList);
        }
    });
    
    // 提交表单
    form.submit();
}

// 更新编辑时的二级分类下拉框
function updateEditSubcategories(categoryId) {
    const subcategorySelect = document.getElementById('add_subcategory_select');
    if (!subcategorySelect) return;
    
    // 清空现有选项（保留第一个"请选择"选项）
    subcategorySelect.innerHTML = '<option value="">-- 请选择二级分类 --</option>';
    
    if (!categoryId || !subcategoriesByCategory) return;
    
    const subcategories = subcategoriesByCategory[categoryId] || [];
    subcategories.forEach(subcat => {
        const option = document.createElement('option');
        option.value = subcat.id;
        const displayText = (subcat.icon ? subcat.icon + ' ' : '') + subcat.name;
        option.textContent = displayText;
        subcategorySelect.appendChild(option);
    });
}

// 在模态框中添加自定义字段
function addCustomFieldInModal() {
    const container = document.getElementById('customFieldsContainer');
    if (!container) {
        alert('找不到自定义字段容器');
        return;
    }
    
    const newField = document.createElement('div');
    newField.className = 'custom-field-item mb-3 p-3 border rounded';
    newField.innerHTML = `
        <input type="hidden" name="existing_custom_field_id[]" value="">
        <div class="row">
            <div class="col-md-3">
                <input type="text" class="form-control" name="custom_field_name[]" placeholder="字段名称（如：背景色）" required>
            </div>
            <div class="col-md-2">
                <select class="form-control" name="custom_field_type[]" onchange="toggleFieldOptionsInModal(this)">
                    <option value="text">文本</option>
                    <option value="number">数字</option>
                    <option value="select">下拉选择</option>
                </select>
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control field-options-simple" name="custom_field_options_simple[]" placeholder="选项（下拉选择时用逗号分隔，如：红底,蓝底,白底）" style="display:none">
                <div class="field-options-manager" style="display:none">
                    <small class="text-muted d-block mb-2">为每个选项配置名称和图片（图片将显示在小程序主图位置）</small>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="addOptionItemInModal(this)">
                        <i class="fas fa-plus"></i> 添加选项
                    </button>
                    <div class="options-list mt-2"></div>
                    <input type="hidden" class="field-options-json" name="custom_field_options[]" value="">
                </div>
            </div>
            <div class="col-md-2">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" name="custom_field_required[]" value="1">
                    <label class="form-check-label">必填</label>
                </div>
            </div>
            <div class="col-md-1">
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeCustomFieldInModal(this)">删除</button>
            </div>
        </div>
    `;
    container.appendChild(newField);
}

// 删除自定义字段
function removeCustomFieldInModal(button) {
    const fieldItem = button.closest('.custom-field-item');
    if (fieldItem) {
        fieldItem.remove();
    }
}

// 切换字段选项显示
function toggleFieldOptionsInModal(select) {
    const fieldItem = select.closest('.custom-field-item');
    if (!fieldItem) return;
    
    const simpleInput = fieldItem.querySelector('.field-options-simple');
    const optionsManager = fieldItem.querySelector('.field-options-manager');
    
    if (select.value === 'select') {
        if (simpleInput) simpleInput.style.display = 'none';
        if (optionsManager) optionsManager.style.display = 'block';
    } else {
        if (simpleInput) simpleInput.style.display = 'none';
        if (optionsManager) optionsManager.style.display = 'none';
    }
}

// 添加选项项
function addOptionItemInModal(button) {
    const optionsList = button.nextElementSibling;
    if (!optionsList || !optionsList.classList.contains('options-list')) {
        console.error('找不到选项列表容器');
        return;
    }
    
    const optionItem = document.createElement('div');
    optionItem.className = 'option-item mb-2 p-2 border rounded';
    optionItem.innerHTML = `
        <div class="row align-items-center">
            <div class="col-md-4">
                <input type="text" class="form-control form-control-sm option-name" placeholder="选项名称" required>
            </div>
            <div class="col-md-5">
                <input type="file" class="form-control form-control-sm option-image" accept="image/*" onchange="handleOptionImageChangeInModal(this)">
                <input type="hidden" class="option-image-url" value="">
                <div class="option-image-preview mt-1">
                    <small class="text-muted">未上传图片</small>
                </div>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeOptionItemInModal(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    optionsList.appendChild(optionItem);
}

// 删除选项项
function removeOptionItemInModal(button) {
    const optionItem = button.closest('.option-item');
    if (optionItem) {
        optionItem.remove();
        updateFieldOptionsJSONInModal(optionItem.closest('.options-list'));
    }
}

// 处理选项图片选择
function handleOptionImageChangeInModal(input) {
    const file = input.files[0];
    const preview = input.closest('.row').querySelector('.option-image-preview');
    const imageUrlInput = input.closest('.row').querySelector('.option-image-url');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview) {
                preview.innerHTML = `<img src="${e.target.result}" alt="选项图片" style="max-width: 60px; max-height: 60px; border-radius: 4px; border: 1px solid #ddd;">`;
            }
        };
        reader.readAsDataURL(file);
    } else {
        const existingUrl = imageUrlInput ? imageUrlInput.value : '';
        if (preview) {
            if (existingUrl) {
                preview.innerHTML = `<img src="${existingUrl}" alt="选项图片" style="max-width: 60px; max-height: 60px; border-radius: 4px; border: 1px solid #ddd;">`;
            } else {
                preview.innerHTML = '<small class="text-muted">未上传图片</small>';
            }
        }
    }
}

// 更新字段选项JSON
function updateFieldOptionsJSONInModal(optionsList) {
    if (!optionsList) return;
    
    const fieldItem = optionsList.closest('.custom-field-item');
    if (!fieldItem) return;
    
    const jsonInput = fieldItem.querySelector('.field-options-json');
    if (!jsonInput) return;
    
    const optionItems = optionsList.querySelectorAll('.option-item');
    const options = [];
    
    optionItems.forEach((item) => {
        const nameInput = item.querySelector('.option-name');
        const imageInput = item.querySelector('.option-image');
        const imageUrlInput = item.querySelector('.option-image-url');
        
        if (nameInput && nameInput.value.trim()) {
            const option = {
                name: nameInput.value.trim()
            };
            
            if (imageInput && imageInput.files && imageInput.files.length > 0) {
                option._hasNewImage = true;
            } else if (imageUrlInput && imageUrlInput.value) {
                option.image_url = imageUrlInput.value;
            }
            
            options.push(option);
        }
    });
    
    jsonInput.value = JSON.stringify(options);
}

// 加载产品自定义字段到编辑表单
function loadProductCustomFieldsForEdit(customFields) {
    const container = document.getElementById('customFieldsContainer');
    if (!container) return;
    
    // 清空现有字段
    container.innerHTML = '';
    
    // 添加自定义字段
    customFields.forEach(field => {
        const fieldItem = document.createElement('div');
        fieldItem.className = 'custom-field-item mb-3 p-3 border rounded';
        
        // 解析选项数据
        let optionsHTML = '';
        if (field.field_type === 'select' && field.field_options) {
            try {
                const optionsData = JSON.parse(field.field_options);
                if (Array.isArray(optionsData)) {
                    optionsData.forEach(opt => {
                        const imageUrl = opt.image_url || '';
                        const imagePreview = imageUrl 
                            ? `<img src="${imageUrl}" alt="选项图片" style="max-width: 60px; max-height: 60px; border-radius: 4px; border: 1px solid #ddd;">`
                            : '<small class="text-muted">未上传图片</small>';
                        
                        optionsHTML += `
                            <div class="option-item mb-2 p-2 border rounded">
                                <div class="row align-items-center">
                                    <div class="col-md-4">
                                        <input type="text" class="form-control form-control-sm option-name" value="${opt.name || ''}" placeholder="选项名称" required>
                                    </div>
                                    <div class="col-md-5">
                                        <input type="file" class="form-control form-control-sm option-image" accept="image/*" onchange="handleOptionImageChangeInModal(this)">
                                        <input type="hidden" class="option-image-url" value="${imageUrl}">
                                        <div class="option-image-preview mt-1">${imagePreview}</div>
                                    </div>
                                    <div class="col-md-2">
                                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeOptionItemInModal(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                }
            } catch (e) {
                // 如果不是JSON格式，按逗号分隔处理
                const optionsList = field.field_options.split(',');
                optionsList.forEach(optName => {
                    optionsHTML += `
                        <div class="option-item mb-2 p-2 border rounded">
                            <div class="row align-items-center">
                                <div class="col-md-4">
                                    <input type="text" class="form-control form-control-sm option-name" value="${optName.trim()}" placeholder="选项名称" required>
                                </div>
                                <div class="col-md-5">
                                    <input type="file" class="form-control form-control-sm option-image" accept="image/*" onchange="handleOptionImageChangeInModal(this)">
                                    <input type="hidden" class="option-image-url" value="">
                                    <div class="option-image-preview mt-1">
                                        <small class="text-muted">未上传图片</small>
                                    </div>
                                </div>
                                <div class="col-md-2">
                                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeOptionItemInModal(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        }
        
        const optionsManagerDisplay = field.field_type === 'select' ? 'block' : 'none';
        
        fieldItem.innerHTML = `
            <input type="hidden" name="existing_custom_field_id[]" value="${field.id}">
            <div class="row">
                <div class="col-md-3">
                    <input type="text" class="form-control" name="custom_field_name[]" value="${field.field_name || ''}" placeholder="字段名称" required>
                </div>
                <div class="col-md-2">
                    <select class="form-control" name="custom_field_type[]" onchange="toggleFieldOptionsInModal(this)">
                        <option value="text" ${field.field_type === 'text' ? 'selected' : ''}>文本</option>
                        <option value="number" ${field.field_type === 'number' ? 'selected' : ''}>数字</option>
                        <option value="select" ${field.field_type === 'select' ? 'selected' : ''}>下拉选择</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <input type="text" class="form-control field-options-simple" name="custom_field_options_simple[]" placeholder="选项（下拉选择时用逗号分隔）" style="display:none">
                    <div class="field-options-manager" style="display:${optionsManagerDisplay}">
                        <small class="text-muted d-block mb-2">为每个选项配置名称和图片（图片将显示在小程序主图位置）</small>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="addOptionItemInModal(this)">
                            <i class="fas fa-plus"></i> 添加选项
                        </button>
                        <div class="options-list mt-2">${optionsHTML}</div>
                        <input type="hidden" class="field-options-json" name="custom_field_options[]" value="${field.field_options || ''}">
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" name="custom_field_required[]" value="1" ${field.is_required ? 'checked' : ''}>
                        <label class="form-check-label">必填</label>
                    </div>
                </div>
                <div class="col-md-1">
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeCustomFieldInModal(this)">删除</button>
                </div>
            </div>
        `;
        container.appendChild(fieldItem);
    });
}

// ========== 二级分类排序功能 ==========
let sortableSubcategories = [];

// 打开排序模态框
function openSortSubcategoryModal() {
    if (!selectedCategoryId) {
        alert('请先选择一级分类');
        return;
    }
    
    // 获取当前一级分类下的所有二级分类
    const categoryId = parseInt(selectedCategoryId);
    const subcategories = subcategoriesByCategory[categoryId] || [];
    
    if (subcategories.length === 0) {
        alert('当前分类下没有二级分类');
        return;
    }
    
    // 按当前排序顺序排序
    subcategories.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
    sortableSubcategories = [...subcategories];
    
    // 渲染可拖拽列表
    renderSortableSubcategoryList();
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('sortSubcategoryModal'));
    modal.show();
}

// 渲染可拖拽的二级分类列表
function renderSortableSubcategoryList() {
    const container = document.getElementById('sortableSubcategories');
    container.innerHTML = '';
    
    sortableSubcategories.forEach((subcategory, index) => {
        const div = document.createElement('div');
        div.className = 'sortable-item';
        div.draggable = true;
        div.dataset.index = index;
        div.innerHTML = `
            <div class="item-info">
                <h6>${subcategory.icon ? subcategory.icon + ' ' : ''}${subcategory.name}</h6>
                <small class="text-muted">${subcategory.code}</small>
            </div>
            <i class="fas fa-grip-vertical drag-handle"></i>
        `;
        
        // 拖拽事件
        div.addEventListener('dragstart', handleSubcategoryDragStart);
        div.addEventListener('dragover', handleSubcategoryDragOver);
        div.addEventListener('drop', handleSubcategoryDrop);
        div.addEventListener('dragend', handleSubcategoryDragEnd);
        
        container.appendChild(div);
    });
}

let draggedSubcategoryElement = null;

function handleSubcategoryDragStart(e) {
    draggedSubcategoryElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleSubcategoryDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    const afterElement = getDragAfterSubcategoryElement(this.parentNode, e.clientY);
    const dragging = document.querySelector('.dragging');
    if (!dragging || dragging === this) return;
    
    if (afterElement == null) {
        this.parentNode.appendChild(dragging);
    } else {
        this.parentNode.insertBefore(dragging, afterElement);
    }
}

function handleSubcategoryDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    if (!draggedSubcategoryElement) return;
    
    // 获取新的顺序
    const container = document.getElementById('sortableSubcategories');
    const items = Array.from(container.querySelectorAll('.sortable-item'));
    const newOrder = items.map(item => {
        const index = parseInt(item.dataset.index);
        return sortableSubcategories[index];
    });
    
    // 更新数组顺序
    sortableSubcategories = newOrder;
    
    // 重新渲染以更新索引
    renderSortableSubcategoryList();
    
    return false;
}

function handleSubcategoryDragEnd(e) {
    this.classList.remove('dragging');
}

function getDragAfterSubcategoryElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.sortable-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// 保存二级分类排序
async function saveSubcategorySortOrder() {
    try {
        // 更新每个二级分类的排序值
        const updates = sortableSubcategories.map((subcategory, index) => ({
            id: subcategory.id,
            sort_order: index
        }));
        
        // 批量更新排序
        for (const update of updates) {
            const response = await fetch(`/api/admin/product-subcategories/${update.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sort_order: update.sort_order
                })
            });
            
            if (!response.ok) {
                const result = await response.json();
                throw new Error(result.message || `更新二级分类 ${update.id} 排序失败`);
            }
        }
        
        // 关闭模态框并刷新
        bootstrap.Modal.getInstance(document.getElementById('sortSubcategoryModal')).hide();
        loadSubcategories(selectedCategoryId);
        alert('排序保存成功');
    } catch (error) {
        console.error('保存排序失败:', error);
        alert('保存排序失败: ' + error.message);
    }
}
