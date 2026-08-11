<template>
  <view class="page-shell page-shell--task">
    <view class="page-content">
      <BrandHeader
        title="我的项目"
        summary="草稿不会进入项目大厅，发布前可以反复检查。"
        caption="项目管理"
        back
      >
        <template #action>
          <button class="header-action" aria-label="创建项目" @click="openPage(routes.projectEdit)">
            <uni-icons type="plusempty" size="22" color="#ffffff" />
          </button>
        </template>
      </BrandHeader>
      <FixtureBanner />

      <view v-if="loading" class="list-loading">
        <view class="list-loading__line" />
        <view class="list-loading__block" />
      </view>

      <view v-else-if="errorView" class="section">
        <StatusPanel
          :title="errorView.title"
          :description="errorView.description"
          tone="error"
          action-label="重试"
          @action="loadProject"
        />
      </view>

      <view v-else-if="!project.id" class="section">
        <StatusPanel
          title="还没有项目草稿"
          description="从一个清晰的问题和一个开放岗位开始。"
          action-label="创建项目"
          @action="openPage(routes.projectEdit)"
        />
      </view>

      <view v-else class="owned-project">
        <view class="owned-project__topline">
          <text class="status-chip" :class="`status-chip--${project.status.toLowerCase()}`">
            {{ statusLabel }}
          </text>
          <text class="owned-project__version">版本 {{ project.version }}</text>
        </view>
        <text class="owned-project__title">{{ project.title || "未命名项目" }}</text>
        <text class="owned-project__description">{{ project.description || "项目简介尚未填写" }}</text>
        <view class="owned-project__meta">
          <text>{{ project.direction || "方向待填写" }}</text>
          <text>{{ openRoleCount }} 个开放岗位</text>
        </view>
        <view class="button-row">
          <button class="secondary-button" @click="openPage(routes.projectEdit)">继续编辑</button>
          <button
            class="primary-button"
            @click="openPage(project.status === 'PUBLISHED' ? routes.projectResult : routes.projectPreview)"
          >
            {{ project.status === "PUBLISHED" ? "查看结果" : "发布预览" }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import { emptyProjectDraft, type ProjectDraft } from "@/domain/models";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { openPage, routes } from "@/utils/navigation";

const loading = ref(true);
const project = ref<ProjectDraft>(emptyProjectDraft());
const errorView = ref<ErrorPresentation | null>(null);

const openRoleCount = computed(() => project.value.roles.filter((role) => role.status === "OPEN").length);
const statusLabel = computed(() => ({ DRAFT: "草稿", PUBLISHED: "已发布", CLOSED: "已关闭" })[project.value.status]);

async function loadProject(): Promise<void> {
  loading.value = true;
  errorView.value = null;
  try {
    project.value = (await repository.getProject()).data;
  } catch (error) {
    errorView.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

onShow(loadProject);
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

.list-loading {
  padding: 42rpx 0;
}

.list-loading__line,
.list-loading__block {
  border-radius: 6rpx;
  background: #e3eae6;
}

.list-loading__line {
  width: 40%;
  height: 25rpx;
}

.list-loading__block {
  height: 260rpx;
  margin-top: 24rpx;
}

.owned-project {
  margin-top: 34rpx;
  padding: 30rpx 0;
  border-top: 1rpx solid #dce4df;
  border-bottom: 1rpx solid #dce4df;
}

.owned-project__topline,
.owned-project__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.status-chip {
  padding: 8rpx 14rpx;
  border-radius: 5rpx;
  font-size: 21rpx;
  font-weight: 700;
}

.status-chip--draft {
  background: #fff3d7;
  color: #87580c;
}

.status-chip--published {
  background: #e7f3ed;
  color: #12664f;
}

.status-chip--closed {
  background: #edf0ee;
  color: #66746e;
}

.owned-project__version,
.owned-project__meta {
  color: #74817b;
  font-size: 22rpx;
}

.owned-project__title {
  display: block;
  margin-top: 22rpx;
  color: #17231e;
  font-size: 36rpx;
  font-weight: 800;
  line-height: 1.35;
}

.owned-project__description {
  display: block;
  margin-top: 12rpx;
  color: #607069;
  font-size: 24rpx;
  line-height: 1.6;
}

.owned-project__meta {
  margin-top: 22rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #e0e7e3;
}
</style>
