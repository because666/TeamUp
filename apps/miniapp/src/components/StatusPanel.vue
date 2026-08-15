<template>
  <view class="status-panel" :class="`status-panel--${tone}`">
    <view class="status-panel__icon">
      <uni-icons :type="icon" size="24" :color="iconColor" />
    </view>
    <view class="status-panel__body">
      <text class="status-panel__title">{{ title }}</text>
      <text v-if="description" class="status-panel__description">{{ description }}</text>
      <button v-if="actionLabel" class="status-panel__action" @click="$emit('action')">
        {{ actionLabel }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    tone?: "neutral" | "error" | "success" | "warning";
    actionLabel?: string;
  }>(),
  { tone: "neutral", description: "", actionLabel: "" },
);

defineEmits<{ (event: "action"): void }>();

const icon = computed(() => {
  if (props.tone === "error") return "clear";
  if (props.tone === "success") return "checkbox-filled";
  if (props.tone === "warning") return "info-filled";
  return "info";
});

const iconColor = computed(() => {
  if (props.tone === "error") return "#b13b2d";
  if (props.tone === "success") return "#12664f";
  if (props.tone === "warning") return "#9a620c";
  return "#607069";
});
</script>

<style scoped>
.status-panel {
  display: flex;
  gap: 18rpx;
  padding: 28rpx;
  border: 1rpx solid #d8e2dd;
  border-radius: 8rpx;
  background: #ffffff;
}

.status-panel--error {
  border-color: #e4b7b1;
  background: #fff8f6;
}

.status-panel--success {
  border-color: #acd1c2;
  background: #f3faf7;
}

.status-panel--warning {
  border-color: #ead5aa;
  background: #fffaf0;
}

.status-panel__icon {
  display: flex;
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  align-items: center;
  justify-content: center;
}

.status-panel__body {
  min-width: 0;
  flex: 1;
}

.status-panel__title {
  display: block;
  color: #26352f;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.45;
}

.status-panel__description {
  display: block;
  margin-top: 8rpx;
  color: #66746e;
  font-size: 23rpx;
  line-height: 1.55;
}

.status-panel__action {
  display: inline-flex;
  width: auto;
  min-height: 68rpx;
  align-items: center;
  justify-content: center;
  margin-top: 18rpx;
  padding: 0 22rpx;
  border: 1rpx solid #b7c8c0;
  border-radius: 8rpx;
  background: #ffffff;
  color: #12664f;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.2;
}
</style>
