<template>
  <view class="page-shell page-shell--task result-page">
    <view class="page-content">
      <BrandHeader caption="项目状态" back />
      <FixtureBanner />

      <view v-if="loading" class="result-loading">
        <view class="result-loading__mark" />
        <view class="result-loading__line result-loading__line--wide" />
        <view class="result-loading__line" />
      </view>

      <view v-else-if="errorView" class="section">
        <StatusPanel
          :title="errorView.title"
          :description="errorDescription"
          tone="error"
          action-label="重新查询状态"
          @action="loadResult"
        />
      </view>

      <template v-else-if="project.status === 'PUBLISHED'">
        <view class="result-hero">
          <view class="result-hero__mark">
            <uni-icons type="checkmarkempty" size="34" color="#ffffff" />
          </view>
          <text class="result-hero__eyebrow">已确认发布状态</text>
          <text class="result-hero__title">项目已发布</text>
          <text class="result-hero__copy">招募信息现在可以进入项目发现与后续匹配流程。</text>
        </view>

        <view class="published-summary">
          <view class="published-summary__topline">
            <text class="published-summary__status">PUBLISHED</text>
            <text class="published-summary__time">{{ publishedTime }}</text>
          </view>
          <text class="published-summary__title">{{ project.title }}</text>
          <text class="published-summary__description">{{ project.description }}</text>
          <view class="published-summary__meta">
            <text>{{ project.direction }}</text>
            <text>{{ openRoleCount }} 个开放岗位</text>
          </view>
        </view>

        <view class="section next-steps">
          <text class="section-title">接下来</text>
          <view class="next-step">
            <view class="next-step__number">1</view>
            <text>在“我的项目”中继续管理项目与岗位。</text>
          </view>
          <view class="next-step">
            <view class="next-step__number">2</view>
            <text>候选人可从开放岗位申请交换联系方式。</text>
          </view>
        </view>

        <view class="button-row result-actions">
          <button class="secondary-button" @click="replacePage(routes.projectEdit)">继续管理</button>
          <button class="primary-button" @click="replacePage(routes.projectList)">返回我的项目</button>
        </view>
      </template>

      <view v-else class="section">
        <StatusPanel
          title="尚未确认发布成功"
          description="当前项目仍是草稿。系统不会根据本地提交动作推断成功。"
          tone="warning"
          action-label="返回发布预览"
          @action="replacePage(routes.projectPreview)"
        />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import { emptyProjectDraft, type ProjectDraft } from "@/domain/models";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { replacePage, routes } from "@/utils/navigation";

const loading = ref(true);
const project = ref<ProjectDraft>(emptyProjectDraft());
const errorView = ref<ErrorPresentation | null>(null);

const openRoleCount = computed(() => project.value.roles.filter((role) => role.status === "OPEN").length);
const publishedTime = computed(() => {
  if (!project.value.publishedAt) return "发布时间待确认";
  return project.value.publishedAt.replace("T", " ").slice(0, 16);
});
const errorDescription = computed(() => {
  if (!errorView.value) return "";
  return errorView.value.requestId === "local_request"
    ? errorView.value.description
    : `${errorView.value.description} 参考号：${errorView.value.requestId}`;
});

async function loadResult(): Promise<void> {
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

onLoad(loadResult);
</script>

<style scoped>
.result-loading {
  display: flex;
  align-items: center;
  flex-direction: column;
  padding: 100rpx 0;
}

.result-loading__mark,
.result-loading__line {
  border-radius: 6rpx;
  background: #e3eae6;
}

.result-loading__mark {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
}

.result-loading__line {
  width: 38%;
  height: 25rpx;
  margin-top: 18rpx;
}

.result-loading__line--wide {
  width: 62%;
  margin-top: 34rpx;
}

.result-hero {
  display: flex;
  align-items: center;
  flex-direction: column;
  padding: 74rpx 0 50rpx;
  text-align: center;
}

.result-hero__mark {
  display: flex;
  width: 98rpx;
  height: 98rpx;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #12664f;
}

.result-hero__eyebrow {
  margin-top: 24rpx;
  color: #12664f;
  font-size: 22rpx;
  font-weight: 700;
}

.result-hero__title {
  margin-top: 10rpx;
  color: #17231e;
  font-size: 46rpx;
  font-weight: 800;
}

.result-hero__copy {
  max-width: 600rpx;
  margin-top: 14rpx;
  color: #607069;
  font-size: 24rpx;
  line-height: 1.6;
}

.published-summary {
  padding: 30rpx;
  border: 1rpx solid #acd1c2;
  border-radius: 8rpx;
  background: #f3faf7;
}

.published-summary__topline,
.published-summary__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.published-summary__status {
  color: #12664f;
  font-size: 20rpx;
  font-weight: 800;
}

.published-summary__time,
.published-summary__meta {
  color: #66746e;
  font-size: 21rpx;
}

.published-summary__title {
  display: block;
  margin-top: 22rpx;
  color: #17231e;
  font-size: 34rpx;
  font-weight: 800;
  line-height: 1.35;
}

.published-summary__description {
  display: block;
  margin-top: 12rpx;
  color: #53625b;
  font-size: 23rpx;
  line-height: 1.6;
}

.published-summary__meta {
  margin-top: 22rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #cfe0d8;
}

.next-steps {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.next-step {
  display: flex;
  min-height: 58rpx;
  align-items: center;
  gap: 16rpx;
  color: #53625b;
  font-size: 23rpx;
  line-height: 1.5;
}

.next-step__number {
  display: flex;
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
  align-items: center;
  justify-content: center;
  border-radius: 5rpx;
  background: #fff0d0;
  color: #80550f;
  font-size: 20rpx;
  font-weight: 800;
}

.result-actions {
  padding-bottom: 12rpx;
}
</style>
