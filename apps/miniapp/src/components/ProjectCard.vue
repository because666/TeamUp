<template>
  <button
    class="project-card surface"
    :aria-label="`查看项目：${project.title}`"
    @click="emit('select', project.id)"
  >
    <view class="project-card__accent" :class="`project-card__accent--${project.accent}`" />
    <view class="project-card__body">
      <view class="project-card__meta-row">
        <text class="project-card__direction">{{ project.direction }}</text>
        <text class="project-card__stage">{{ project.stage }}</text>
      </view>
      <text class="project-card__title">{{ project.title }}</text>
      <text class="project-card__summary">{{ project.summary }}</text>
      <view class="project-card__tags">
        <text v-for="skill in project.skills" :key="skill" class="project-card__tag">
          {{ skill }}
        </text>
      </view>
      <view class="project-card__footer">
        <text>{{ project.openRoleCount }} 个开放岗位</text>
        <view class="project-card__footer-action">
          <text>{{ project.timeLabel }}</text>
          <uni-icons type="right" size="16" color="#607069" />
        </view>
      </view>
    </view>
  </button>
</template>

<script setup lang="ts">
import type { DiscoveryProject } from "@/domain/models";

defineProps<{ project: DiscoveryProject }>();
const emit = defineEmits<{ (event: "select", projectId: string): void }>();
</script>

<style scoped>
.project-card {
  position: relative;
  display: flex;
  width: 100%;
  overflow: hidden;
  padding: 0;
  color: inherit;
  line-height: normal;
  text-align: left;
}

.project-card:active {
  background: #f1f7f4;
  transform: translateY(1rpx);
}

.project-card__accent {
  width: 10rpx;
  flex: 0 0 10rpx;
}

.project-card__accent--green {
  background: #16815e;
}

.project-card__accent--coral {
  background: #df6653;
}

.project-card__accent--yellow {
  background: #d2a33e;
}

.project-card__body {
  min-width: 0;
  flex: 1;
  padding: 28rpx;
}

.project-card__meta-row,
.project-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.project-card__direction,
.project-card__stage {
  color: #65736d;
  font-size: 21rpx;
  font-weight: 600;
}

.project-card__title {
  display: block;
  margin-top: 16rpx;
  color: #17231e;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1.35;
}

.project-card__summary {
  display: -webkit-box;
  overflow: hidden;
  margin-top: 12rpx;
  color: #5d6b65;
  font-size: 24rpx;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.project-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 20rpx;
}

.project-card__tag {
  padding: 8rpx 14rpx;
  border-radius: 5rpx;
  background: #eef3f0;
  color: #3d5148;
  font-size: 20rpx;
  font-weight: 600;
}

.project-card__footer {
  margin-top: 24rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #e0e7e3;
  color: #74817b;
  font-size: 21rpx;
}

.project-card__footer-action {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: flex-end;
  gap: 6rpx;
}
</style>
