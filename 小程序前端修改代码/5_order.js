// 文件：pages/order/order.js
// 订单页面修改示例

const visitTracker = require('../../utils/visitTracker');

Page({
    data: {
        orderData: null,
        orderId: null
    },

    onLoad: function(options) {
        const productId = options.productId;
        
        console.log('订单页面加载', options);
        
        // 记录订单页面访问
        visitTracker.onPageVisit('pages/order/order', {
            productId: productId,
            options: options
        });
        
        // 加载订单数据
        this.loadOrderData(productId);
    },

    onShow: function() {
        console.log('订单页面显示');
        
        // 记录页面显示
        visitTracker.onPageVisit('pages/order/order', {
            orderId: this.data.orderId,
            action: 'show'
        });
    },

    loadOrderData: function(productId) {
        // 加载订单数据的逻辑...
        console.log('加载订单数据:', productId);
        
        // 模拟订单数据
        this.setData({
            orderData: {
                productId: productId,
                quantity: 1,
                price: 100,
                total: 100
            },
            orderId: 'ORDER_' + Date.now()
        });
    },

    // 提交订单
    submitOrder: function() {
        const orderData = this.data.orderData;
        
        // 记录下单访问
        visitTracker.onOrder(orderData);
        
        // 执行提交订单逻辑...
        console.log('提交订单:', orderData);
        
        wx.showToast({
            title: '订单提交成功',
            icon: 'success'
        });
        
        // 跳转到订单成功页面
        wx.navigateTo({
            url: `/pages/order-success/order-success?orderId=${this.data.orderId}`
        });
    },

    // 取消订单
    cancelOrder: function() {
        const orderId = this.data.orderId;
        
        // 记录取消订单操作
        visitTracker.onPageVisit('pages/order/order', {
            orderId: orderId,
            action: 'cancelOrder'
        });
        
        // 执行取消订单逻辑...
        console.log('取消订单:', orderId);
        
        wx.showModal({
            title: '确认取消',
            content: '确定要取消这个订单吗？',
            success: (res) => {
                if (res.confirm) {
                    wx.showToast({
                        title: '订单已取消',
                        icon: 'success'
                    });
                    
                    // 返回上一页
                    wx.navigateBack();
                }
            }
        });
    }
});








