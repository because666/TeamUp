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
  max-width: 372rpx;
  height: 88rpx;
  overflow: hidden;
  border: 1rpx solid #bfd0c8;
  border-radius: 8rpx;
  background: #ffffff;
  grid-template-columns: 88rpx minmax(0, 1fr) 88rpx;
}

.number-stepper__button {
  display: flex;
  min-height: 88rpx;
  align-items: center;
  justify-content: center;
  border-radius: 0;
  background: #f4f8f6;
  line-height: 1;
}

.number-stepper__button:active {
  background: #e4efe9;
}

.number-stepper__value {
  display: flex;
  min-width: 0;
  align-items: baseline;
  justify-content: center;
  gap: 8rpx;
  border-right: 1rpx solid #dfe6e2;
  border-left: 1rpx solid #dfe6e2;
}

.number-stepper__number {
  color: #17231e;
  font-size: 30rpx;
  font-weight: 800;
}

.number-stepper__unit {
  color: #74817b;
  font-size: 21rpx;
}
</style>
