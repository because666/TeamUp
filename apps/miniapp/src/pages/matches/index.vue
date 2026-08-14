<template>
  <view class="page-shell">
    <view class="page-content">
      <BrandHeader title="匹配" summary="推荐会给出结构化依据，最终选择始终由你决定。" />
      <FixtureBanner />

      <view class="match-summary">
        <view class="match-summary__metric">
          <text class="match-summary__value">0</text>
          <text class="match-summary__label">待处理推荐</text>
        </view>
        <view class="match-summary__divider" />
        <view class="match-summary__metric">
          <text class="match-summary__value">规则</text>
          <text class="match-summary__label">当前推荐方式</text>
        </view>
      </view>

      <view class="section">
        <StatusPanel
          title="暂无可展示的匹配结果"
          description="匹配服务与解释字段需等待双方确认契约；当前页面不会虚构推荐分数。"
          action-label="完善能力名片"
          @action="openPage(routes.profileEdit)"
        />
      </view>
    </view>
    <BottomNav active="matches" />
  </view>
</template>

<script setup lang="ts">
import BottomNav from "@/components/BottomNav.vue";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import { openPage, routes } from "@/utils/navigation";
</script>

<style scoped>
.match-summary {
  display: grid;
  margin-top: 30rpx;
  padding: 30rpx 0;
  border-top: 1rpx solid #dce4df;
  border-bottom: 1rpx solid #dce4df;
  grid-template-columns: 1fr 1rpx 1fr;
}

.match-summary__metric {
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 8rpx;
}

.match-summary__divider {
  background: #dce4df;
}

.match-summary__value {
  color: #12664f;
  font-size: 35rpx;
  font-weight: 800;
}

.match-summary__label {
  color: #74817b;
  font-size: 21rpx;
}
</style>
