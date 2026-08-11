<template>
  <view v-if="fixture" class="fixture-banner">
    <uni-icons type="info" size="16" color="#7a4e09" />
    <text class="fixture-banner__text">合约模拟 · 非真实服务</text>
  </view>
</template>

<script setup lang="ts">
import { isFixtureMode } from "@/services/runtime";

const fixture = isFixtureMode();
</script>

<style scoped>
.fixture-banner {
  display: inline-flex;
  min-height: 54rpx;
  align-items: center;
  gap: 10rpx;
  padding: 0 18rpx;
  border: 1rpx solid #e8cf9a;
  border-radius: 6rpx;
  background: #fff8e9;
}

.fixture-banner__text {
  color: #7a4e09;
  font-size: 21rpx;
  font-weight: 600;
}
</style>
