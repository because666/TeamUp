<template>
  <view class="progress-rail" aria-label="流程进度">
    <view
      v-for="(item, index) in items"
      :key="item"
      class="progress-rail__item"
      :class="{
        'progress-rail__item--done': index + 1 < current,
        'progress-rail__item--active': index + 1 === current,
      }"
    >
      <view class="progress-rail__marker">
        <uni-icons
          v-if="index + 1 < current"
          type="checkmarkempty"
          size="14"
          color="#ffffff"
        />
        <text v-else>{{ index + 1 }}</text>
      </view>
      <text class="progress-rail__label">{{ item }}</text>
      <view v-if="index < items.length - 1" class="progress-rail__line" />
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{ current: number }>();

const items = ["登录", "名片", "项目"];
</script>

<style scoped>
.progress-rail {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 24rpx 0 30rpx;
}

.progress-rail__item {
  position: relative;
  display: flex;
  min-width: 0;
  align-items: center;
  flex-direction: column;
  gap: 9rpx;
  color: #8a9690;
}

.progress-rail__marker {
  position: relative;
  z-index: 2;
  display: flex;
  width: 42rpx;
  height: 42rpx;
  align-items: center;
  justify-content: center;
  border: 2rpx solid #cad5cf;
  border-radius: 50%;
  background: #f4f7f5;
  font-size: 21rpx;
  font-weight: 700;
}

.progress-rail__item--active,
.progress-rail__item--done {
  color: #12664f;
}

.progress-rail__item--active .progress-rail__marker {
  border-color: #12664f;
  background: #ffffff;
}

.progress-rail__item--done .progress-rail__marker {
  border-color: #12664f;
  background: #12664f;
}

.progress-rail__label {
  font-size: 21rpx;
  font-weight: 600;
}

.progress-rail__line {
  position: absolute;
  top: 20rpx;
  left: calc(50% + 28rpx);
  z-index: 1;
  width: calc(100% - 56rpx);
  height: 2rpx;
  background: #cad5cf;
}

.progress-rail__item--done .progress-rail__line {
  background: #12664f;
}
</style>
