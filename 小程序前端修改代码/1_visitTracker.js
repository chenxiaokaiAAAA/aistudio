// 文件：utils/visitTracker.js
// 访问追踪工具类

class VisitTracker {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.promotionCode = null;
        this.referrerUserId = null;
        this.scene = null;
        this.userInfo = null;
        this.openId = null;
        this.userId = null;
        this.isInitialized = false;
    }

    // 生成会话ID
    generateSessionId() {
        return 'SESSION_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // 初始化访问追踪
    async init(options = {}) {
        try {
            if (this.isInitialized) {
                return;
            }

            // 获取小程序启动参数
            const launchOptions = wx.getLaunchOptionsSync();
            
            // 解析场景值
            if (launchOptions.scene) {
                this.scene = launchOptions.scene.toString();
                
                // 解析推广码参数
                if (launchOptions.query) {
                    this.promotionCode = launchOptions.query.promotionCode || null;
                    this.referrerUserId = launchOptions.query.referrerUserId || null;
                }
            }

            // 记录启动访问
            await this.recordVisit('launch', {
                scene: this.scene,
                promotionCode: this.promotionCode,
                referrerUserId: this.referrerUserId,
                pagePath: launchOptions.path || ''
            });

            this.isInitialized = true;
            console.log('✅ 访问追踪初始化成功', {
                sessionId: this.sessionId,
                promotionCode: this.promotionCode,
                scene: this.scene
            });

        } catch (error) {
            console.error('❌ 访问追踪初始化失败:', error);
        }
    }

    // 用户授权后更新信息
    async onUserAuthorize(userInfo) {
        try {
            this.userInfo = userInfo;
            
            // 记录授权访问
            await this.recordVisit('auth', {
                userInfo: userInfo
            });

            console.log('✅ 用户授权记录成功');

        } catch (error) {
            console.error('❌ 用户授权记录失败:', error);
        }
    }

    // 记录页面访问
    async onPageVisit(pagePath, pageData = {}) {
        try {
            await this.recordVisit('browse', {
                pagePath: pagePath,
                pageData: pageData
            });

            console.log('✅ 页面访问记录成功:', pagePath);

        } catch (error) {
            console.error('❌ 页面访问记录失败:', error);
        }
    }

    // 记录下单访问
    async onOrder(orderData) {
        try {
            await this.recordVisit('order', {
                orderData: orderData
            });

            console.log('✅ 下单访问记录成功');

        } catch (error) {
            console.error('❌ 下单访问记录失败:', error);
        }
    }

    // 核心访问记录方法
    async recordVisit(visitType, extraData = {}) {
        try {
            const visitData = {
                sessionId: this.sessionId,
                openId: this.openId,
                userId: this.userId,
                visitType: visitType,
                promotionCode: this.promotionCode,
                referrerUserId: this.referrerUserId,
                scene: this.scene,
                userInfo: this.userInfo,
                pagePath: extraData.pagePath || '',
                ...extraData
            };

            const response = await wx.request({
                url: 'https://moeart.cc/api/user/visit', // 替换为您的实际域名
                method: 'POST',
                data: visitData,
                header: {
                    'Content-Type': 'application/json'
                },
                timeout: 10000 // 10秒超时
            });

            if (response.data && response.data.success) {
                // 更新推广码（如果是新用户）
                if (response.data.promotionCode) {
                    this.promotionCode = response.data.promotionCode;
                }
                
                return response.data;
            } else {
                throw new Error(response.data?.message || '访问记录失败');
            }

        } catch (error) {
            console.error('❌ 访问记录API调用失败:', error);
            // 不抛出错误，避免影响正常业务流程
            return null;
        }
    }

    // 获取当前会话信息
    getSessionInfo() {
        return {
            sessionId: this.sessionId,
            promotionCode: this.promotionCode,
            referrerUserId: this.referrerUserId,
            scene: this.scene,
            userInfo: this.userInfo,
            openId: this.openId,
            userId: this.userId
        };
    }
}

// 导出单例
const visitTracker = new VisitTracker();

module.exports = visitTracker;








