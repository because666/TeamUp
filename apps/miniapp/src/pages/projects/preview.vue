<template>
  <view class="page-shell page-shell--task">
    <view class="page-content">
      <BrandHeader
        title="发布预览"
        summary="以下内容会进入项目大厅，请从候选成员的视角再检查一次。"
        caption="公开前确认"
        back
      />
      <FixtureBanner />

      <view v-if="loading" class="preview-loading">
        <view class="preview-loading__line" />
        <view class="preview-loading__block" />
        <view class="preview-loading__block preview-loading__block--short" />
      </view>

      <view v-else-if="errorView" class="section">
        <StatusPanel
          :title="errorView.title"
          :description="errorDescription"
          :tone="errorView.kind === 'conflict' ? 'warning' : 'error'"
          :action-label="errorActionLabel"
          @action="handleErrorAction"
        />
      </view>

      <template v-else-if="project.id">
        <view v-if="missingItems.length" class="preview-status">
          <StatusPanel
            title="暂时不能发布"
            :description="`请返回编辑页补充 ${missingItems.length} 项必填信息。`"
            tone="warning"
            action-label="返回编辑"
            @action="returnToEdit"
          />
          <view class="missing-list surface">
            <view v-for="item in missingItems" :key="item.key" class="missing-list__item">
              <uni-icons type="info" size="17" color="#9a620c" />
              <text>{{ item.label }}：{{ item.message }}</text>
            </view>
          </view>
        </view>

        <view class="project-preview">
          <view class="project-preview__topline">
            <text class="project-preview__direction">{{ project.direction || "方向待填写" }}</text>
            <text class="project-preview__stage">{{ stageLabel }}</text>
          </view>
          <text class="project-preview__title">{{ project.title || "未命名项目" }}</text>
          <text class="project-preview__description">{{ project.description || "项目简介尚未填写" }}</text>
          <view class="project-preview__facts">
            <view>
              <text class="project-preview__fact-label">适配赛事</text>
              <text class="project-preview__fact-value">{{ project.competition || "未指定" }}</text>
            </view>
            <view>
              <text class="project-preview__fact-label">现有团队</text>
              <text class="project-preview__fact-value">{{ project.teamInfo || "暂未填写" }}</text>
            </view>
          </view>
        </view>

        <view class="section">
          <text class="section-title">开放岗位</text>
          <text class="section-copy">仅开放状态的岗位会对外展示。</text>
          <view class="preview-roles">
            <view
              v-for="(role, index) in openRoles"
              :key="`${role.name}-${index}`"
              class="preview-role surface"
            >
              <view class="preview-role__header">
                <text class="preview-role__title">{{ role.name || `未命名岗位 ${index + 1}` }}</text>
                <text class="preview-role__count">招 {{ role.headcount }} 人</text>
              </view>
              <text class="preview-role__time">每周约 {{ role.hoursPerWeek }} 小时</text>
              <view class="preview-role__skills">
                <text v-for="skill in role.skills" :key="skill">{{ skill }}</text>
                <text v-if="role.skills.length === 0" class="preview-role__empty">技能待填写</text>
              </view>
              <text v-if="role.description" class="preview-role__description">{{ role.description }}</text>
            </view>
          </view>
        </view>

        <view class="section disclosure">
          <uni-icons type="eye" size="21" color="#12664f" />
          <view>
            <text class="disclosure__title">发布后可见范围</text>
            <text class="disclosure__copy">
              项目标题、简介、方向、阶段、团队说明与开放岗位将进入公开项目列表；草稿版本信息不会公开。
            </text>
          </view>
        </view>

        <view class="task-actions">
          <view class="button-row task-actions__buttons">
            <button class="secondary-button" :disabled="publishing" @click="returnToEdit">返回编辑</button>
            <button
              class="primary-button"
              :disabled="publishing || missingItems.length > 0"
              @click="publish"
            >
              {{ publishing ? "正在发布…" : "确认发布" }}
            </button>
          </view>
          <text class="task-actions__meta">发布命令在提交期间只会触发一次</text>
        </view>
      </template>

      <view v-else class="section">
        <StatusPanel
          title="没有可预览的已保存草稿"
          description="先创建并保存项目，再进入发布预览。"
          action-label="返回编辑"
          @action="returnToEdit"
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
import { validateProject } from "@/domain/validation";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { openPage, replacePage, routes } from "@/utils/navigation";

const loading = ref(true);
const publishing = ref(false);
const project = ref<ProjectDraft>(emptyProjectDraft());
const errorView = ref<ErrorPresentation | null>(null);

const fieldLabels: Record<string, string> = {
  "PJ-TITLE": "项目标题",
  "PJ-DESCRIPTION": "项目简介",
  "PJ-DIRECTION": "项目方向",
  "PJ-STAGE": "项目阶段",
  "ROLE-LIST": "开放岗位",
};
const stageLabels: Record<string, string> = {
  IDEA: "想法阶段",
  VALIDATION: "需求验证",
  PROTOTYPE: "原型验证",
  DEVELOPMENT: "开发中",
};

const stageLabel = computed(() => stageLabels[project.value.stage] || project.value.stage);
const openRoles = computed(() => project.value.roles.filter((role) => role.status === "OPEN"));
const missingItems = computed(() => Object.entries(validateProject(project.value)).map(([key, message]) => ({
  key,
  label: fieldLabels[key] || roleFieldLabel(key),
  message,
})));
const errorDescription = computed(() => {
  if (!errorView.value) return "";
  return errorView.value.requestId === "local_request"
    ? errorView.value.description
    : `${errorView.value.description} 参考号：${errorView.value.requestId}`;
});
const errorActionLabel = computed(() => {
  if (errorView.value?.kind === "unauthenticated") return "重新登录";
  if (errorView.value?.kind === "forbidden") return "返回我的项目";
  if (errorView.value?.kind === "validation_error") return "返回编辑";
  return "重新查询";
});

function roleFieldLabel(key: string): string {
  const match = key.match(/^ROLE-(\d+)-(.+)$/);
  if (!match) return "岗位信息";
  const suffix: Record<string, string> = {
    NAME: "岗位名称",
    SKILLS: "岗位技能",
    HEADCOUNT: "招募人数",
    HOURS: "投入时间",
  };
  return `岗位 ${match[1]} · ${suffix[match[2]] || "岗位信息"}`;
}

async function loadProject(): Promise<void> {
  loading.value = true;
  errorView.value = null;
  try {
    const response = await repository.getProject();
    project.value = response.data;
    if (project.value.status === "PUBLISHED") replacePage(routes.projectResult);
  } catch (error) {
    errorView.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

async function publish(): Promise<void> {
  if (publishing.value || missingItems.value.length) return;
  publishing.value = true;
  errorView.value = null;
  try {
    const response = await repository.publishProject(project.value);
    project.value = response.data;
    replacePage(routes.projectResult);
  } catch (error) {
    errorView.value = presentError(error);
    uni.pageScrollTo({ scrollTop: 0, duration: 240 });
  } finally {
    publishing.value = false;
  }
}

function returnToEdit(): void {
  if (getCurrentPages().length > 1) uni.navigateBack();
  else replacePage(routes.projectEdit);
}

function handleErrorAction(): void {
  if (errorView.value?.kind === "unauthenticated") replacePage(routes.login);
  else if (errorView.value?.kind === "forbidden") replacePage(routes.projectList);
  else if (errorView.value?.kind === "validation_error") returnToEdit();
  else void loadProject();
}

onLoad(loadProject);
</script>

<style scoped>
.preview-loading {
  padding: 40rpx 0;
}

.preview-loading__line,
.preview-loading__block {
  border-radius: 6rpx;
  background: #e3eae6;
}

.preview-loading__line {
  width: 38%;
  height: 26rpx;
}

.preview-loading__block {
  height: 260rpx;
  margin-top: 24rpx;
}

.preview-loading__block--short {
  height: 180rpx;
}

.preview-status {
  margin-top: 28rpx;
}

.missing-list {
  margin-top: 16rpx;
  padding: 12rpx 24rpx;
}

.missing-list__item {
  display: flex;
  min-height: 64rpx;
  align-items: center;
  gap: 12rpx;
  border-top: 1rpx solid #e7ece9;
  color: #695124;
  font-size: 22rpx;
  line-height: 1.45;
}

.missing-list__item:first-child {
  border-top: 0;
}

.project-preview {
  padding: 36rpx 0;
  border-bottom: 1rpx solid #dce4df;
}

.project-preview__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.project-preview__direction,
.project-preview__stage {
  color: #12664f;
  font-size: 22rpx;
  font-weight: 700;
}

.project-preview__title {
  display: block;
  margin-top: 18rpx;
  color: #17231e;
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1.3;
}

.project-preview__description {
  display: block;
  margin-top: 18rpx;
  color: #53625b;
  font-size: 25rpx;
  line-height: 1.7;
}

.project-preview__facts {
  display: grid;
  gap: 18rpx;
  margin-top: 28rpx;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.project-preview__facts > view {
  padding: 20rpx;
  border-left: 6rpx solid #d5a841;
  background: #fffaf0;
}

.project-preview__fact-label,
.project-preview__fact-value {
  display: block;
}

.project-preview__fact-label {
  color: #80601e;
  font-size: 20rpx;
  font-weight: 700;
}

.project-preview__fact-value {
  margin-top: 8rpx;
  color: #3d413a;
  font-size: 23rpx;
  line-height: 1.45;
}

.preview-roles {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 24rpx;
}

.preview-role {
  padding: 26rpx;
}

.preview-role__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.preview-role__title {
  color: #26352f;
  font-size: 28rpx;
  font-weight: 800;
}

.preview-role__count {
  flex: 0 0 auto;
  color: #12664f;
  font-size: 21rpx;
  font-weight: 700;
}

.preview-role__time {
  display: block;
  margin-top: 8rpx;
  color: #74817b;
  font-size: 21rpx;
}

.preview-role__skills {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.preview-role__skills text {
  padding: 8rpx 13rpx;
  border-radius: 5rpx;
  background: #eaf3ef;
  color: #12664f;
  font-size: 20rpx;
  font-weight: 700;
}

.preview-role__skills .preview-role__empty {
  background: #f0f2f1;
  color: #74817b;
}

.preview-role__description {
  display: block;
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid #e0e7e3;
  color: #607069;
  font-size: 23rpx;
  line-height: 1.55;
}

.disclosure {
  display: flex;
  gap: 18rpx;
}

.disclosure__title,
.disclosure__copy {
  display: block;
}

.disclosure__title {
  color: #26352f;
  font-size: 25rpx;
  font-weight: 700;
}

.disclosure__copy {
  margin-top: 8rpx;
  color: #66746e;
  font-size: 22rpx;
  line-height: 1.55;
}

.task-actions {
  padding: 32rpx 0 12rpx;
  border-top: 1rpx solid #dce4df;
}

.task-actions__buttons {
  margin-top: 0;
}

.task-actions__meta {
  display: block;
  margin-top: 14rpx;
  color: #74817b;
  font-size: 21rpx;
  text-align: center;
}
</style>
