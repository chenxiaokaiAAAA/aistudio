// 文件：pages/product/product.js
// 商品页面修改示例

const visitTracker = require('../../utils/visitTracker');

Page({
    data: {
        productId: null,
        productInfo: null
    },

    onLoad: function(options) {
        const productId = options.id;
        this.setData({ productId });
        
        console.log('商品页面加载', options);
        
        // 记录商品页面访问
        visitTracker.onPageVisit('pages/product/product', {
            productId: productId,
            options: options
        });
        
        // 加载商品信息
        this.loadProductInfo(productId);
    },

    onShow: function() {
        console.log('商品页面显示');
        
        // 记录页面显示
        visitTracker.onPageVisit('pages/product/product', {
            productId: this.data.productId,
            action: 'show'
        });
    },

    onHide: function() {
        console.log('商品页面隐藏');
    },

    loadProductInfo: function(productId) {
        // 加载商品信息的逻辑...
        console.log('加载商品信息:', productId);
        
        // 模拟商品数据
        this.setData({
            productInfo: {
                id: productId,
                name: '商品名称',
                price: 100,
                image: 'https://example.com/image.jpg'
            }
        });
    },

    // 添加到购物车
    addToCart: function() {
        const productId = this.data.productId;
        
        // 记录购物车操作
        visitTracker.onPageVisit('pages/product/product', {
            productId: productId,
            action: 'addToCart'
        });
        
        // 执行添加到购物车逻辑...
        console.log('添加到购物车:', productId);
        
        wx.showToast({
            title: '已添加到购物车',
            icon: 'success'
        });
    },

    // 立即购买
    buyNow: function() {
        const productId = this.data.productId;
        
        // 记录立即购买操作
        visitTracker.onPageVisit('pages/product/product', {
            productId: productId,
            action: 'buyNow'
        });
        
        // 执行立即购买逻辑...
        console.log('立即购买:', productId);
        
        // 跳转到订单页面
        wx.navigateTo({
            url: `/pages/order/order?productId=${productId}`
        });
    }
});








