<template>
  <view v-if="visible" class="confirm-dialog" role="dialog" aria-modal="true">
    <view class="confirm-dialog__backdrop" @click="$emit('cancel')" />
    <view class="confirm-dialog__panel">
      <view class="confirm-dialog__icon">
        <uni-icons type="info-filled" size="22" color="#12664f" />
      </view>
      <text class="confirm-dialog__title">{{ title }}</text>
      <text class="confirm-dialog__description">{{ description }}</text>
      <view class="confirm-dialog__actions">
        <button class="confirm-dialog__cancel" @click="$emit('cancel')">{{ cancelLabel }}</button>
        <button class="confirm-dialog__confirm" @click="$emit('confirm')">{{ confirmLabel }}</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    visible: boolean;
    title: string;
    description: string;
    confirmLabel?: string;
    cancelLabel?: string;
  }>(),
  { confirmLabel: "确认", cancelLabel: "取消" },
);

defineEmits<{ (event: "confirm"): void; (event: "cancel"): void }>();
</script>

<style scoped>
.confirm-dialog {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 44rpx;
}

.confirm-dialog__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(20, 32, 27, 0.5);
}

.confirm-dialog__panel {
  position: relative;
  width: 100%;
  max-width: 580rpx;
  overflow: hidden;
  border-radius: 8rpx;
  background: #ffffff;
  box-shadow: 0 18rpx 42rpx rgba(20, 32, 27, 0.2);
}

.confirm-dialog__icon {
  display: flex;
  width: 64rpx;
  height: 64rpx;
  align-items: center;
  justify-content: center;
  margin: 34rpx 32rpx 0;
  border-radius: 50%;
  background: #eaf3ef;
}

.confirm-dialog__title {
  display: block;
  margin: 20rpx 32rpx 0;
  color: #17231e;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1.35;
}

.confirm-dialog__description {
  display: block;
  margin: 14rpx 32rpx 30rpx;
  color: #65736d;
  font-size: 25rpx;
  line-height: 1.6;
}

.confirm-dialog__actions {
  display: grid;
  border-top: 1rpx solid #dfe6e2;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.confirm-dialog__cancel,
.confirm-dialog__confirm {
  display: flex;
  min-height: 92rpx;
  align-items: center;
  justify-content: center;
  border-radius: 0;
  background: #ffffff;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1.2;
}

.confirm-dialog__cancel {
  border-right: 1rpx solid #dfe6e2;
  color: #52625b;
}

.confirm-dialog__confirm {
  color: #12664f;
}

.confirm-dialog__cancel:active {
  background: #f4f7f5;
}

.confirm-dialog__confirm:active {
  background: #eaf3ef;
}
</style>
