// 文件：pages/index/index.js
// 首页修改示例

const visitTracker = require('../../utils/visitTracker');

Page({
    data: {
        userInfo: null,
        hasUserInfo: false
    },

    onLoad: function(options) {
        console.log('首页加载', options);
        
        // 记录页面访问
        visitTracker.onPageVisit('pages/index/index', {
            options: options
        });
    },

    onShow: function() {
        console.log('首页显示');
        
        // 记录页面显示
        visitTracker.onPageVisit('pages/index/index', {
            action: 'show'
        });
    },

    onHide: function() {
        console.log('首页隐藏');
    },

    // 用户授权
    getUserProfile: function() {
        wx.getUserProfile({
            desc: '用于完善用户资料',
            success: (res) => {
                this.setData({
                    userInfo: res.userInfo,
                    hasUserInfo: true
                });
                
                // 记录用户授权
                visitTracker.onUserAuthorize(res.userInfo);
                
                // 保存到全局
                getApp().globalData.userInfo = res.userInfo;
            },
            fail: (err) => {
                console.error('用户授权失败:', err);
            }
        });
    },

    // 下单按钮点击
    createOrder: function() {
        // 模拟下单数据
        const orderData = {
            productId: '123',
            quantity: 1,
            price: 100,
            timestamp: Date.now()
        };
        
        // 记录下单访问
        visitTracker.onOrder(orderData);
        
        // 执行下单逻辑...
        console.log('下单成功');
        
        // 跳转到订单页面
        wx.navigateTo({
            url: '/pages/order/order'
        });
    },

    // 浏览商品
    viewProduct: function(e) {
        const productId = e.currentTarget.dataset.id;
        
        // 记录商品浏览
        visitTracker.onPageVisit('pages/index/index', {
            action: 'viewProduct',
            productId: productId
        });
        
        // 跳转到商品详情
        wx.navigateTo({
            url: `/pages/product/product?id=${productId}`
        });
    }
});








