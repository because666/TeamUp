<template>
  <view class="page-shell">
    <view class="page-content">
      <BrandHeader title="发现协作机会" summary="先看项目需要什么，再决定要不要加入。">
        <template #action>
          <button class="header-action" aria-label="发布项目" @click="openPage(routes.projectEdit)">
            <uni-icons type="plusempty" size="22" color="#ffffff" />
          </button>
        </template>
      </BrandHeader>

      <FixtureBanner />

      <view class="discover-tools">
        <view class="search-field">
          <uni-icons type="search" size="19" color="#74817b" />
          <input v-model="query" class="search-field__input" placeholder="搜索项目方向或技能" />
        </view>
        <view class="segment" aria-label="发现类型">
          <button
            v-for="item in segments"
            :key="item.key"
            class="segment__button"
            :class="{ 'segment__button--active': segment === item.key }"
            @click="segment = item.key"
          >
            {{ item.label }}
          </button>
        </view>
      </view>

      <view v-if="!fixture" class="section">
        <StatusPanel
          title="真实项目服务尚未接入"
          description="当前构建不会展示合约模拟数据。"
          tone="warning"
        />
      </view>

      <view v-else-if="segment === 'talent'" class="section">
        <StatusPanel
          title="人才发现将在后续任务开放"
          description="当前切片先完成能力名片与项目发布。"
        />
      </view>

      <view v-else class="project-list">
        <view class="list-heading">
          <text class="list-heading__title">正在招募</text>
          <text class="list-heading__count">{{ filteredProjects.length }} 个项目</text>
        </view>
        <StatusPanel
          v-if="filteredProjects.length === 0"
          title="没有找到相关项目"
          description="换一个方向或技能关键词试试。"
        />
        <ProjectCard
          v-for="project in filteredProjects"
          v-else
          :key="project.id"
          :project="project"
          @select="openProjectDetail"
        />
      </view>
    </view>
    <BottomNav active="discover" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import BottomNav from "@/components/BottomNav.vue";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import ProjectCard from "@/components/ProjectCard.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import { discoveryProjects } from "@/domain/fixtures";
import { isFixtureMode } from "@/services/runtime";
import { openPage, projectDetailRoute, routes } from "@/utils/navigation";

const fixture = isFixtureMode();
const query = ref("");
const segment = ref<"project" | "talent">("project");
const segments = [
  { key: "project" as const, label: "找项目" },
  { key: "talent" as const, label: "找队友" },
];

function openProjectDetail(projectId: string): void {
  openPage(projectDetailRoute(projectId));
}

const filteredProjects = computed(() => {
  if (!fixture) return [];
  const keyword = query.value.trim().toLowerCase();
  if (!keyword) return discoveryProjects;
  return discoveryProjects.filter((project) =>
    [project.title, project.direction, project.stage, project.summary, ...project.skills]
      .join(" ")
      .toLowerCase()
      .includes(keyword),
  );
});
</script>

<style scoped>
.header-action {
  display: flex;
  width: 68rpx;
  height: 68rpx;
  flex: 0 0 68rpx;
  align-items: center;
  justify-content: center;
  border-radius: 8rpx;
  background: #12664f;
  line-height: 1;
}

.discover-tools {
  padding: 28rpx 0 8rpx;
}

.search-field {
  display: flex;
  height: 88rpx;
  align-items: center;
  gap: 14rpx;
  padding: 0 24rpx;
  border: 1rpx solid #cfd9d3;
  border-radius: 8rpx;
  background: #ffffff;
}

.search-field__input {
  min-width: 0;
  height: 86rpx;
  flex: 1;
  color: #17231e;
  font-size: 26rpx;
}

.segment {
  display: grid;
  height: 80rpx;
  margin-top: 20rpx;
  padding: 6rpx;
  border: 1rpx solid #d5ded9;
  border-radius: 8rpx;
  background: #e9efec;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.segment__button {
  min-height: 66rpx;
  border-radius: 6rpx;
  background: transparent;
  color: #66746e;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 66rpx;
}

.segment__button--active {
  background: #ffffff;
  color: #12664f;
  box-shadow: 0 2rpx 8rpx rgba(33, 52, 44, 0.08);
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  padding: 34rpx 0;
}

.list-heading {
  display: flex;
  min-height: 52rpx;
  align-items: baseline;
  justify-content: space-between;
  gap: 20rpx;
}

.list-heading__title {
  color: #17231e;
  font-size: 32rpx;
  font-weight: 800;
}

.list-heading__count {
  color: #74817b;
  font-size: 22rpx;
}
</style>
