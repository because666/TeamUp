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
  gap: 14rpx;
}

.tag-selector__item {
  display: inline-flex;
  width: auto;
  min-height: 70rpx;
  align-items: center;
  gap: 7rpx;
  padding: 0 22rpx;
  border: 1rpx solid #cad5cf;
  border-radius: 6rpx;
  background: #ffffff;
  color: #435149;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 70rpx;
}

.tag-selector__item--selected {
  border-color: #12664f;
  background: #12664f;
  color: #ffffff;
}
</style>
