<template>
  <view class="number-stepper">
    <button class="number-stepper__button" aria-label="减少" @click="change(-step)">
      <uni-icons type="minus" size="18" color="#244038" />
    </button>
    <view class="number-stepper__value">
      <text class="number-stepper__number">{{ modelValue }}</text>
      <text class="number-stepper__unit">{{ unit }}</text>
    </view>
    <button class="number-stepper__button" aria-label="增加" @click="change(step)">
      <uni-icons type="plus" size="18" color="#244038" />
    </button>
  </view>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: number;
    min?: number;
    max?: number;
    step?: number;
    unit?: string;
  }>(),
  { min: 1, max: 40, step: 1, unit: "" },
);

const emit = defineEmits<{ (event: "update:modelValue", value: number): void }>();

function change(delta: number): void {
  emit("update:modelValue", Math.min(props.max, Math.max(props.min, props.modelValue + delta)));
}
</script>

<style scoped>
.number-stepper {
  display: grid;
  width: 100%;
  max-width: 360rpx;
  height: 80rpx;
  overflow: hidden;
  border: 1rpx solid #cbd6d0;
  border-radius: 8rpx;
  background: #ffffff;
  grid-template-columns: 80rpx 1fr 80rpx;
}

.number-stepper__button {
  display: flex;
  min-height: 80rpx;
  align-items: center;
  justify-content: center;
  border-radius: 0;
  background: #f4f7f5;
  line-height: 1;
}

.number-stepper__value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 7rpx;
  border-right: 1rpx solid #dce4df;
  border-left: 1rpx solid #dce4df;
}

.number-stepper__number {
  color: #17231e;
  font-size: 29rpx;
  font-weight: 800;
}

.number-stepper__unit {
  color: #74817b;
  font-size: 21rpx;
}
</style>
