<template>
  <view class="page-shell">
    <view class="page-content">
      <BrandHeader title="消息" summary="项目沟通与邀请会集中出现在这里。" />
      <FixtureBanner />

      <view class="message-tabs">
        <button class="message-tabs__item message-tabs__item--active">会话</button>
        <button class="message-tabs__item">邀请</button>
      </view>

      <view class="section">
        <StatusPanel
          title="还没有消息"
          description="消息与邀请接口尚未进入当前 P0 切片。"
        />
      </view>
    </view>
    <BottomNav active="messages" />
  </view>
</template>

<script setup lang="ts">
import BottomNav from "@/components/BottomNav.vue";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
</script>

<style scoped>
.message-tabs {
  display: flex;
  gap: 28rpx;
  margin-top: 28rpx;
  border-bottom: 1rpx solid #dce4df;
}

.message-tabs__item {
  position: relative;
  width: auto;
  min-height: 82rpx;
  padding: 0 4rpx;
  border-radius: 0;
  background: transparent;
  color: #74817b;
  font-size: 25rpx;
  font-weight: 700;
  line-height: 82rpx;
}

.message-tabs__item--active {
  color: #12664f;
}

.message-tabs__item--active::after {
  position: absolute;
  right: 0;
  bottom: -1rpx;
  left: 0;
  height: 5rpx;
  border-radius: 3rpx 3rpx 0 0;
  background: #12664f;
  content: "";
}
</style>
