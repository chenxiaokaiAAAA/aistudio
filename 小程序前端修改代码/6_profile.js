// 文件：pages/profile/profile.js
// 个人中心页面修改示例

const visitTracker = require('../../utils/visitTracker');

Page({
    data: {
        userInfo: null,
        hasUserInfo: false
    },

    onLoad: function(options) {
        console.log('个人中心页面加载', options);
        
        // 记录页面访问
        visitTracker.onPageVisit('pages/profile/profile', {
            options: options
        });
        
        // 加载用户信息
        this.loadUserInfo();
    },

    onShow: function() {
        console.log('个人中心页面显示');
        
        // 记录页面显示
        visitTracker.onPageVisit('pages/profile/profile', {
            action: 'show'
        });
    },

    loadUserInfo: function() {
        // 从全局数据获取用户信息
        const app = getApp();
        if (app.globalData.userInfo) {
            this.setData({
                userInfo: app.globalData.userInfo,
                hasUserInfo: true
            });
        }
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

    // 查看订单
    viewOrders: function() {
        // 记录查看订单操作
        visitTracker.onPageVisit('pages/profile/profile', {
            action: 'viewOrders'
        });
        
        // 跳转到订单列表
        wx.navigateTo({
            url: '/pages/order-list/order-list'
        });
    },

    // 查看推广码
    viewPromotionCode: function() {
        // 记录查看推广码操作
        visitTracker.onPageVisit('pages/profile/profile', {
            action: 'viewPromotionCode'
        });
        
        // 跳转到推广码页面
        wx.navigateTo({
            url: '/pages/promotion/promotion'
        });
    },

    // 联系客服
    contactService: function() {
        // 记录联系客服操作
        visitTracker.onPageVisit('pages/profile/profile', {
            action: 'contactService'
        });
        
        // 执行联系客服逻辑...
        console.log('联系客服');
        
        wx.showToast({
            title: '正在联系客服...',
            icon: 'loading'
        });
    }
});








