<template>
  <view class="brand-header">
    <view class="brand-header__row">
      <button v-if="back" class="brand-header__back" aria-label="返回" @click="goBack">
        <uni-icons type="left" size="22" color="#21322b" />
      </button>
      <view v-else class="brand-mark" aria-hidden="true">
        <view class="brand-mark__cell brand-mark__cell--a" />
        <view class="brand-mark__cell brand-mark__cell--b" />
      </view>

      <view class="brand-header__identity">
        <text class="brand-header__brand">TeamUp</text>
        <text v-if="caption" class="brand-header__caption">{{ caption }}</text>
      </view>

      <slot name="action" />
    </view>

    <view v-if="title" class="brand-header__title-row">
      <text class="brand-header__title">{{ title }}</text>
      <text v-if="summary" class="brand-header__summary">{{ summary }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
const props = defineProps<{
  title?: string;
  summary?: string;
  caption?: string;
  back?: boolean;
  manualBack?: boolean;
}>();

const emit = defineEmits<{ (event: "back"): void }>();

function goBack(): void {
  if (props.manualBack) {
    emit("back");
    return;
  }
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack();
  } else {
    uni.reLaunch({ url: "/pages/me/index" });
  }
}
</script>

<style scoped>
.brand-header {
  width: 100%;
  padding-top: max(24rpx, env(safe-area-inset-top));
}

.brand-header__row {
  display: flex;
  min-height: 82rpx;
  align-items: center;
  gap: 18rpx;
}

.brand-header__back,
.brand-mark {
  flex: 0 0 68rpx;
  width: 68rpx;
  height: 68rpx;
}

.brand-header__back {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid #d6e0db;
  border-radius: 50%;
  background: #ffffff;
  line-height: 1;
}

.brand-mark {
  position: relative;
  border-radius: 8rpx;
  background: #173d32;
}

.brand-mark__cell {
  position: absolute;
  width: 24rpx;
  height: 24rpx;
  border-radius: 3rpx;
}

.brand-mark__cell--a {
  top: 14rpx;
  left: 14rpx;
  background: #f0c45b;
}

.brand-mark__cell--b {
  right: 14rpx;
  bottom: 14rpx;
  background: #ee725e;
}

.brand-header__identity {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}

.brand-header__brand {
  color: #173d32;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.15;
}

.brand-header__caption {
  margin-top: 5rpx;
  color: #74817b;
  font-size: 20rpx;
  line-height: 1.2;
}

.brand-header__title-row {
  padding: 34rpx 0 28rpx;
}

.brand-header__title {
  display: block;
  color: #17231e;
  font-size: 48rpx;
  font-weight: 800;
  line-height: 1.22;
}

.brand-header__summary {
  display: block;
  max-width: 660rpx;
  margin-top: 14rpx;
  color: #607069;
  font-size: 26rpx;
  line-height: 1.6;
}
</style>
