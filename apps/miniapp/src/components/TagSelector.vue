<template>
  <view class="tag-selector">
    <button
      v-for="option in options"
      :key="option"
      class="tag-selector__item"
      :class="{ 'tag-selector__item--selected': modelValue.includes(option) }"
      @click="toggle(option)"
    >
      <uni-icons
        v-if="modelValue.includes(option)"
        type="checkmarkempty"
        size="14"
        color="#ffffff"
      />
      <text>{{ option }}</text>
    </button>
  </view>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: string[];
  options: string[];
  single?: boolean;
}>();

const emit = defineEmits<{ (event: "update:modelValue", value: string[]): void }>();

function toggle(option: string): void {
  if (props.single) {
    emit("update:modelValue", props.modelValue.includes(option) ? [] : [option]);
    return;
  }
  const next = props.modelValue.includes(option)
    ? props.modelValue.filter((item) => item !== option)
    : [...props.modelValue, option];
  emit("update:modelValue", next);
}
</script>

<style scoped>
.tag-selector {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 14rpx 12rpx;
}

.tag-selector__item {
  display: inline-flex;
  width: auto;
  min-height: 72rpx;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  gap: 7rpx;
  padding: 0 20rpx;
  border: 1rpx solid #c7d3cd;
  border-radius: 8rpx;
  background: #ffffff;
  color: #435149;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1.2;
}

.tag-selector__item--selected {
  border-color: #12664f;
  background: #12664f;
  color: #ffffff;
}

.tag-selector__item:active {
  border-color: #12664f;
  background: #eaf3ef;
  color: #12664f;
}

.tag-selector__item--selected:active {
  background: #0e5743;
  color: #ffffff;
}
</style>
