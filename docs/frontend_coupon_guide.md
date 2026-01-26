# 用户自主领取优惠券 - 前端配置指南

## 🎯 功能概述

用户可以在小程序中自主领取优惠券，无需后台人工派发。系统会自动验证优惠券的有效性、用户领取限制等。

## 📋 后端配置完成情况

### ✅ 已完成的配置

1. **数据库表创建**
   - `coupons` 表：存储优惠券信息
   - `user_coupons` 表：存储用户领取记录
   - 相关索引已创建

2. **API接口实现**
   - `/api/coupons/available` - 获取可领取优惠券列表
   - `/api/coupons/get` - 用户领取优惠券
   - `/api/coupons/user/<user_id>` - 获取用户优惠券列表

3. **示例数据**
   - 已创建示例优惠券数据
   - 包含不同类型的优惠券（现金券、折扣券、免费券）

## 🚀 前端需要实现的页面和功能

### 1. 优惠券领取页面

```javascript
// 页面路径建议：pages/coupon/claim
Page({
  data: {
    availableCoupons: [],  // 可领取的优惠券列表
    userCoupons: [],       // 用户已领取的优惠券
    loading: false
  },

  onLoad() {
    this.loadAvailableCoupons();
    this.loadUserCoupons();
  },

  // 加载可领取的优惠券
  async loadAvailableCoupons() {
    try {
      this.setData({ loading: true });
      
      const userId = this.getUserId();
      const response = await wx.request({
        url: `${app.globalData.apiBase}/api/coupons/available`,
        method: 'GET',
        data: { userId: userId }
      });

      if (response.data.success) {
        this.setData({
          availableCoupons: response.data.data
        });
      } else {
        wx.showToast({
          title: response.data.message,
          icon: 'none'
        });
      }
    } catch (error) {
      console.error('加载优惠券失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 领取优惠券
  async claimCoupon(e) {
    const couponId = e.currentTarget.dataset.couponId;
    const couponName = e.currentTarget.dataset.couponName;
    
    try {
      wx.showLoading({ title: '领取中...' });
      
      const userId = this.getUserId();
      const response = await wx.request({
        url: `${app.globalData.apiBase}/api/coupons/get`,
        method: 'POST',
        data: {
          userId: userId,
          couponId: couponId
        }
      });

      if (response.data.success) {
        wx.showToast({
          title: '领取成功',
          icon: 'success'
        });
        
        // 重新加载数据
        this.loadAvailableCoupons();
        this.loadUserCoupons();
      } else {
        wx.showToast({
          title: response.data.message,
          icon: 'none'
        });
      }
    } catch (error) {
      console.error('领取优惠券失败:', error);
      wx.showToast({
        title: '领取失败',
        icon: 'none'
      });
    } finally {
      wx.hideLoading();
    }
  },

  // 获取用户ID
  getUserId() {
    // 根据你的用户系统调整
    const userId = wx.getStorageSync('userId');
    if (userId) return userId;
    
    // 如果没有用户ID，生成一个临时ID
    const tempUserId = 'USER' + Date.now();
    wx.setStorageSync('userId', tempUserId);
    return tempUserId;
  }
});
```

### 2. 优惠券列表页面

```javascript
// 页面路径建议：pages/coupon/list
Page({
  data: {
    userCoupons: [],
    activeTab: 'unused'  // unused, used, expired
  },

  onLoad() {
    this.loadUserCoupons();
  },

  // 切换标签页
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    this.loadUserCoupons();
  },

  // 加载用户优惠券
  async loadUserCoupons() {
    try {
      const userId = this.getUserId();
      const status = this.data.activeTab;
      
      const response = await wx.request({
        url: `${app.globalData.apiBase}/api/coupons/user/${userId}`,
        method: 'GET',
        data: { status: status }
      });

      if (response.data.success) {
        this.setData({
          userCoupons: response.data.data
        });
      }
    } catch (error) {
      console.error('加载用户优惠券失败:', error);
    }
  }
});
```

### 3. WXML 模板示例

```xml
<!-- 优惠券领取页面 -->
<view class="coupon-claim-page">
  <view class="page-title">优惠券中心</view>
  
  <!-- 可领取优惠券 -->
  <view class="section">
    <view class="section-title">可领取优惠券</view>
    <view class="coupon-list">
      <view 
        class="coupon-item" 
        wx:for="{{availableCoupons}}" 
        wx:key="id"
        wx:if="{{item.can_claim}}"
      >
        <view class="coupon-content">
          <view class="coupon-name">{{item.name}}</view>
          <view class="coupon-desc">{{item.description}}</view>
          <view class="coupon-value">
            <text wx:if="{{item.type === 'cash'}}">¥{{item.value}}</text>
            <text wx:elif="{{item.type === 'discount'}}">{{item.value}}%</text>
            <text wx:elif="{{item.type === 'free'}}">免费</text>
          </view>
          <view class="coupon-condition">满¥{{item.min_amount}}可用</view>
        </view>
        <view class="coupon-action">
          <button 
            class="claim-btn" 
            data-coupon-id="{{item.id}}"
            data-coupon-name="{{item.name}}"
            bindtap="claimCoupon"
          >
            领取
          </button>
        </view>
      </view>
    </view>
  </view>

  <!-- 已领取优惠券 -->
  <view class="section">
    <view class="section-title">我的优惠券</view>
    <view class="coupon-list">
      <view 
        class="coupon-item used" 
        wx:for="{{userCoupons}}" 
        wx:key="id"
      >
        <view class="coupon-content">
          <view class="coupon-name">{{item.coupon_name}}</view>
          <view class="coupon-code">{{item.coupon_code}}</view>
          <view class="coupon-status">
            <text wx:if="{{item.status === 'unused'}}">未使用</text>
            <text wx:elif="{{item.status === 'used'}}">已使用</text>
            <text wx:elif="{{item.status === 'expired'}}">已过期</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</view>
```

### 4. WXSS 样式示例

```css
/* 优惠券页面样式 */
.coupon-claim-page {
  padding: 20rpx;
  background-color: #f5f5f5;
}

.page-title {
  font-size: 36rpx;
  font-weight: bold;
  text-align: center;
  margin-bottom: 30rpx;
}

.section {
  margin-bottom: 40rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
  color: #333;
}

.coupon-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.coupon-item {
  display: flex;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  padding: 30rpx;
  color: white;
  position: relative;
  overflow: hidden;
}

.coupon-item.used {
  background: linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%);
}

.coupon-content {
  flex: 1;
}

.coupon-name {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 10rpx;
}

.coupon-desc {
  font-size: 24rpx;
  opacity: 0.8;
  margin-bottom: 10rpx;
}

.coupon-value {
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 10rpx;
}

.coupon-condition {
  font-size: 24rpx;
  opacity: 0.8;
}

.coupon-action {
  display: flex;
  align-items: center;
}

.claim-btn {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2rpx solid white;
  border-radius: 8rpx;
  padding: 16rpx 32rpx;
  font-size: 28rpx;
}

.claim-btn:active {
  background-color: rgba(255, 255, 255, 0.3);
}
```

## 🔧 API 接口说明

### 1. 获取可领取优惠券

```javascript
// 请求
GET /api/coupons/available?userId=USER0655561914

// 响应
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "新用户专享券",
      "code": "NEWUSER10",
      "type": "cash",
      "value": 10.0,
      "min_amount": 50.0,
      "description": "新用户专享，满50元减10元",
      "start_time": "2025-10-21T00:00:00",
      "end_time": "2025-10-31T23:59:59",
      "total_count": 1000,
      "used_count": 0,
      "remaining_count": 1000,
      "per_user_limit": 1,
      "user_claimed_count": 0,
      "can_claim": true,
      "status": "active"
    }
  ],
  "total": 1
}
```

### 2. 领取优惠券

```javascript
// 请求
POST /api/coupons/get
{
  "userId": "USER0655561914",
  "couponId": 1
}

// 响应
{
  "success": true,
  "message": "领取成功"
}
```

### 3. 获取用户优惠券列表

```javascript
// 请求
GET /api/coupons/user/USER0655561914?status=unused

// 响应
{
  "success": true,
  "data": [
    {
      "coupon_id": 1,
      "coupon_name": "新用户专享券",
      "coupon_code": "NEWUSER10",
      "coupon_type": "cash",
      "coupon_value": 10.0,
      "min_amount": 50.0,
      "status": "unused",
      "get_time": "2025-10-21T12:00:00",
      "expire_time": "2025-10-31T23:59:59"
    }
  ]
}
```

## 🎯 关键功能点

1. **用户ID管理**：确保每个用户有唯一的ID
2. **优惠券验证**：后端会自动验证优惠券的有效性
3. **领取限制**：支持每用户限领数量
4. **状态管理**：优惠券有未使用、已使用、已过期等状态
5. **实时更新**：领取后立即更新UI显示

## 🚀 部署步骤

1. **运行数据库脚本**：`python create_coupon_tables.py`
2. **重启后端服务**：确保新的API接口生效
3. **前端页面开发**：按照上述代码示例开发页面
4. **测试功能**：测试优惠券领取和使用流程

现在用户就可以在小程序中自主领取优惠券了！🎉


