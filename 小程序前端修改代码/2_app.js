// 文件：app.js
// 小程序主入口文件修改

const visitTracker = require('./utils/visitTracker');

App({
    onLaunch: function(options) {
        console.log('小程序启动', options);
        
        // 初始化访问追踪
        visitTracker.init(options);
    },

    onShow: function(options) {
        console.log('小程序显示', options);
        
        // 每次显示都记录访问
        visitTracker.recordVisit('launch', {
            scene: options.scene,
            pagePath: options.path || ''
        });
    },

    onHide: function() {
        console.log('小程序隐藏');
    },

    globalData: {
        visitTracker: visitTracker,
        userInfo: null
    }
});








