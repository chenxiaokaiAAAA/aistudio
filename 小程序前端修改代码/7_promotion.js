// 文件：pages/promotion/promotion.js
// 推广码页面修改示例

const visitTracker = require('../../utils/visitTracker');

Page({
    data: {
        promotionCode: null,
        qrCodeUrl: null
    },

    onLoad: function(options) {
        console.log('推广码页面加载', options);
        
        // 记录页面访问
        visitTracker.onPageVisit('pages/promotion/promotion', {
            options: options
        });
        
        // 加载推广码信息
        this.loadPromotionInfo();
    },

    onShow: function() {
        console.log('推广码页面显示');
        
        // 记录页面显示
        visitTracker.onPageVisit('pages/promotion/promotion', {
            action: 'show'
        });
    },

    loadPromotionInfo: function() {
        // 获取当前用户的推广码
        const sessionInfo = visitTracker.getSessionInfo();
        
        this.setData({
            promotionCode: sessionInfo.promotionCode || '暂无推广码',
            qrCodeUrl: this.generateQRCode(sessionInfo.promotionCode)
        });
    },

    // 生成二维码
    generateQRCode: function(promotionCode) {
        if (!promotionCode) {
            return null;
        }
        
        // 这里需要调用二维码生成服务
        // 示例：https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=your-promotion-code
        return `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${promotionCode}`;
    },

    // 复制推广码
    copyPromotionCode: function() {
        const promotionCode = this.data.promotionCode;
        
        if (!promotionCode || promotionCode === '暂无推广码') {
            wx.showToast({
                title: '暂无推广码',
                icon: 'none'
            });
            return;
        }
        
        // 记录复制推广码操作
        visitTracker.onPageVisit('pages/promotion/promotion', {
            action: 'copyPromotionCode',
            promotionCode: promotionCode
        });
        
        // 复制到剪贴板
        wx.setClipboardData({
            data: promotionCode,
            success: () => {
                wx.showToast({
                    title: '推广码已复制',
                    icon: 'success'
                });
            }
        });
    },

    // 分享推广码
    sharePromotionCode: function() {
        const promotionCode = this.data.promotionCode;
        
        // 记录分享推广码操作
        visitTracker.onPageVisit('pages/promotion/promotion', {
            action: 'sharePromotionCode',
            promotionCode: promotionCode
        });
        
        // 执行分享逻辑
        console.log('分享推广码:', promotionCode);
        
        wx.showToast({
            title: '分享功能开发中',
            icon: 'none'
        });
    },

    // 查看推广数据
    viewPromotionData: function() {
        // 记录查看推广数据操作
        visitTracker.onPageVisit('pages/promotion/promotion', {
            action: 'viewPromotionData'
        });
        
        // 跳转到推广数据页面
        wx.navigateTo({
            url: '/pages/promotion-data/promotion-data'
        });
    }
});








