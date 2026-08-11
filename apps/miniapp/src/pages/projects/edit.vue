<template>
  <view class="page-shell page-shell--task">
    <view class="page-content">
      <BrandHeader
        title="项目与岗位"
        summary="先保存草稿，再从公开视角检查招募信息。"
        caption="项目草稿"
        back
        manual-back
        @back="requestLeave"
      />
      <ProgressRail :current="3" />
      <FixtureBanner />

      <view v-if="loading" class="form-loading">
        <view v-for="index in 5" :key="index" class="form-loading__row">
          <view class="form-loading__label" />
          <view class="form-loading__control" />
        </view>
      </view>

      <view v-else-if="loadError" class="section">
        <StatusPanel
          :title="loadError.title"
          :description="errorDescription(loadError)"
          tone="error"
          :action-label="loadError.kind === 'unauthenticated' ? '重新登录' : '重新加载'"
          @action="handleLoadError"
        />
      </view>

      <template v-else>
        <view v-if="submitError" class="form-status">
          <StatusPanel
            :title="submitError.title"
            :description="errorDescription(submitError)"
            :tone="submitError.kind === 'conflict' ? 'warning' : 'error'"
            :action-label="submitError.kind === 'conflict' ? '重新加载' : '重试保存'"
            @action="submitError.kind === 'conflict' ? loadProject() : saveDraft()"
          />
        </view>

        <view v-if="Object.keys(errors).length" class="form-status">
          <StatusPanel
            title="发布信息还不完整"
            :description="`当前有 ${Object.keys(errors).length} 项需要补充；草稿仍可保存。`"
            tone="warning"
          />
        </view>

        <view class="section">
          <view class="section-heading">
            <view>
              <text class="section-title">项目说明</text>
              <text class="section-copy">公开内容保持具体，让候选成员能判断是否合适。</text>
            </view>
            <text class="draft-version">版本 {{ draft.version }}</text>
          </view>

          <view class="field">
            <text class="field-label">项目标题 *</text>
            <input
              v-model="draft.title"
              class="text-input"
              maxlength="48"
              placeholder="一句话说清项目要做什么"
            />
            <text v-if="errors['PJ-TITLE']" class="field-error">{{ errors["PJ-TITLE"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">项目简介 *</text>
            <textarea
              v-model="draft.description"
              class="text-area text-area--project"
              maxlength="600"
              placeholder="要解决的问题、当前方案和希望达成的结果"
            />
            <view class="field-counter">
              <text v-if="errors['PJ-DESCRIPTION']" class="field-error">{{ errors["PJ-DESCRIPTION"] }}</text>
              <text>{{ draft.description.length }}/600</text>
            </view>
          </view>

          <view class="field">
            <text class="field-label">项目方向 *</text>
            <TagSelector
              :model-value="draft.direction ? [draft.direction] : []"
              :options="directionOptions"
              single
              @update:model-value="setDirection"
            />
            <text v-if="errors['PJ-DIRECTION']" class="field-error">{{ errors["PJ-DIRECTION"] }}</text>
          </view>

          <view class="field field-grid">
            <view class="field-grid__item">
              <text class="field-label">项目阶段 *</text>
              <picker :range="stageLabels" :value="stageIndex" @change="selectStage">
                <view class="picker-control">
                  <text>{{ currentStageLabel }}</text>
                  <uni-icons type="down" size="17" color="#74817b" />
                </view>
              </picker>
            </view>
            <view class="field-grid__item">
              <text class="field-label">适配赛事</text>
              <input v-model="draft.competition" class="text-input" maxlength="60" placeholder="选填" />
            </view>
          </view>

          <view class="field">
            <text class="field-label">现有团队信息</text>
            <textarea
              v-model="draft.teamInfo"
              class="text-area"
              maxlength="240"
              placeholder="例如：已有产品与设计各 1 人"
            />
          </view>
        </view>

        <view class="section role-section">
          <view class="section-heading">
            <view>
              <text class="section-title">招募岗位</text>
              <text class="section-copy">至少保留一个信息完整的开放岗位。</text>
            </view>
            <text class="role-count">{{ draft.roles.length }} 个</text>
          </view>

          <view v-for="(role, index) in draft.roles" :key="index" class="role-editor">
            <view class="role-editor__header">
              <view class="role-editor__number">{{ index + 1 }}</view>
              <text class="role-editor__title">岗位 {{ index + 1 }}</text>
              <button
                v-if="draft.roles.length > 1"
                class="role-editor__remove"
                aria-label="移除岗位"
                @click="removeRole(index)"
              >
                <uni-icons type="trash" size="19" color="#a5372a" />
              </button>
            </view>

            <view class="field">
              <text class="field-label">岗位名称 *</text>
              <input v-model="role.name" class="text-input" maxlength="36" placeholder="例如：前端开发" />
              <text v-if="errors[`ROLE-${index + 1}-NAME`]" class="field-error">
                {{ errors[`ROLE-${index + 1}-NAME`] }}
              </text>
            </view>

            <view class="field">
              <text class="field-label">所需技能 *</text>
              <TagSelector v-model="role.skills" :options="skillOptions" />
              <text v-if="errors[`ROLE-${index + 1}-SKILLS`]" class="field-error">
                {{ errors[`ROLE-${index + 1}-SKILLS`] }}
              </text>
            </view>

            <view class="field field-grid">
              <view class="field-grid__item">
                <text class="field-label">招募人数 *</text>
                <NumberStepper v-model="role.headcount" :min="1" :max="12" unit="人" />
                <text v-if="errors[`ROLE-${index + 1}-HEADCOUNT`]" class="field-error">
                  {{ errors[`ROLE-${index + 1}-HEADCOUNT`] }}
                </text>
              </view>
              <view class="field-grid__item">
                <text class="field-label">每周投入 *</text>
                <NumberStepper v-model="role.hoursPerWeek" :min="1" :max="40" unit="小时" />
                <text v-if="errors[`ROLE-${index + 1}-HOURS`]" class="field-error">
                  {{ errors[`ROLE-${index + 1}-HOURS`] }}
                </text>
              </view>
            </view>

            <view class="field">
              <text class="field-label">岗位说明</text>
              <textarea
                v-model="role.description"
                class="text-area"
                maxlength="240"
                placeholder="主要任务、预期产出和协作方式"
              />
            </view>

            <view class="role-status">
              <view>
                <text class="role-status__title">开放招募</text>
                <text class="role-status__copy">关闭的岗位不会进入发布条件计算。</text>
              </view>
              <switch
                :checked="role.status === 'OPEN'"
                color="#12664f"
                @change="changeRoleStatus(index, $event)"
              />
            </view>
          </view>

          <button class="secondary-button add-role-button" @click="addRole">
            <uni-icons type="plusempty" size="19" color="#12664f" />
            <text>添加岗位</text>
          </button>
          <text v-if="errors['ROLE-LIST']" class="field-error">{{ errors["ROLE-LIST"] }}</text>
        </view>

        <view class="task-actions">
          <view class="button-row task-actions__buttons">
            <button class="secondary-button" :disabled="saving" @click="saveDraft()">
              {{ saving ? "正在保存…" : "保存草稿" }}
            </button>
            <button class="primary-button" :disabled="saving" @click="saveAndPreview">
              保存并预览
            </button>
          </view>
          <text class="task-actions__meta">
            {{ dirty ? "有未保存修改 · 已保存在本机用于恢复" : savedLabel }}
          </text>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { onBackPress, onLoad } from "@dcloudio/uni-app";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import NumberStepper from "@/components/NumberStepper.vue";
import ProgressRail from "@/components/ProgressRail.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import TagSelector from "@/components/TagSelector.vue";
import {
  emptyProjectDraft,
  type FieldErrors,
  type ProjectDraft,
  type RecruitmentRoleDraft,
} from "@/domain/models";
import { validateProject } from "@/domain/validation";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { recoveryStorage } from "@/services/storage";
import { openPage, replacePage, routes } from "@/utils/navigation";

const directionOptions = ["校园服务", "绿色科技", "文化创意", "人工智能", "社会创新", "生命健康"];
const skillOptions = ["产品设计", "UI 设计", "Vue", "Java", "Python", "数据分析", "内容策划", "运营"];
const stageOptions = [
  { value: "IDEA", label: "想法阶段" },
  { value: "VALIDATION", label: "需求验证" },
  { value: "PROTOTYPE", label: "原型验证" },
  { value: "DEVELOPMENT", label: "开发中" },
];
const stageLabels = stageOptions.map((item) => item.label);

const draft = reactive<ProjectDraft>(emptyProjectDraft());
const errors = ref<FieldErrors>({});
const loading = ref(true);
const saving = ref(false);
const ready = ref(false);
const confirmedSnapshot = ref("");
const loadError = ref<ErrorPresentation | null>(null);
const submitError = ref<ErrorPresentation | null>(null);
let allowLeave = false;

const stageIndex = computed(() => Math.max(0, stageOptions.findIndex((item) => item.value === draft.stage)));
const currentStageLabel = computed(() => stageOptions[stageIndex.value]?.label || "选择阶段");
const dirty = computed(() => ready.value && JSON.stringify(draft) !== confirmedSnapshot.value);
const savedLabel = computed(() => draft.id ? `已保存版本 ${draft.version}` : "尚未保存到服务端");

function replaceDraft(value: ProjectDraft): void {
  const cloned = JSON.parse(JSON.stringify(value)) as ProjectDraft;
  Object.assign(draft, cloned);
  draft.roles.splice(0, draft.roles.length, ...cloned.roles);
}

function confirmDialog(title: string, content: string, confirmText: string, cancelText: string): Promise<boolean> {
  return new Promise((resolve) => {
    uni.showModal({
      title,
      content,
      confirmText,
      cancelText,
      success: (result) => resolve(result.confirm),
      fail: () => resolve(false),
    });
  });
}

function errorDescription(error: ErrorPresentation): string {
  return error.requestId === "local_request"
    ? error.description
    : `${error.description} 参考号：${error.requestId}`;
}

async function loadProject(): Promise<void> {
  loading.value = true;
  ready.value = false;
  loadError.value = null;
  submitError.value = null;
  try {
    const response = await repository.getProject();
    const serverDraft = response.data;
    replaceDraft(serverDraft);
    confirmedSnapshot.value = JSON.stringify(serverDraft);

    const recovery = recoveryStorage.readProject();
    if (recovery && JSON.stringify(recovery) !== confirmedSnapshot.value) {
      const restore = await confirmDialog(
        "发现未保存草稿",
        "上次编辑可能被中断，是否恢复保存在本机的项目内容？",
        "恢复草稿",
        "使用已保存版本",
      );
      if (restore) replaceDraft(recovery);
      else recoveryStorage.clearProject();
    }
    ready.value = true;
  } catch (error) {
    loadError.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

function setDirection(value: string[]): void {
  draft.direction = value[0] || "";
}

function selectStage(event: { detail: { value: string | number } }): void {
  draft.stage = stageOptions[Number(event.detail.value)]?.value || "IDEA";
}

function addRole(): void {
  draft.roles.push({
    name: "",
    skills: [],
    headcount: 1,
    hoursPerWeek: 6,
    description: "",
    status: "OPEN",
  });
}

async function removeRole(index: number): Promise<void> {
  const confirmed = await confirmDialog(
    "移除这个岗位？",
    "岗位中尚未保存的内容会一并移除。",
    "确认移除",
    "保留岗位",
  );
  if (confirmed) draft.roles.splice(index, 1);
}

function changeRoleStatus(index: number, event: Event): void {
  const role = draft.roles[index];
  const checked = (event as Event & { detail: { value: boolean } }).detail.value;
  if (role) role.status = checked ? "OPEN" : "CLOSED";
}

async function saveDraft(exitAfter = false): Promise<boolean> {
  if (saving.value) return false;
  saving.value = true;
  submitError.value = null;
  try {
    const response = await repository.saveProject(draft);
    replaceDraft(response.data);
    confirmedSnapshot.value = JSON.stringify(response.data);
    recoveryStorage.clearProject();
    uni.showToast({ title: "草稿已保存", icon: "success" });
    if (exitAfter) {
      leaveEditor();
    }
    return true;
  } catch (error) {
    submitError.value = presentError(error);
    return false;
  } finally {
    saving.value = false;
  }
}

async function saveAndPreview(): Promise<void> {
  if (saving.value) return;
  errors.value = validateProject(draft);
  const saved = await saveDraft();
  if (saved) openPage(routes.projectPreview);
}

function handleLoadError(): void {
  if (loadError.value?.kind === "unauthenticated") replacePage(routes.login);
  else void loadProject();
}

function leaveEditor(): void {
  allowLeave = true;
  if (getCurrentPages().length > 1) uni.navigateBack();
  else replacePage(routes.projectList);
}

function requestLeave(): void {
  if (allowLeave || !dirty.value) {
    leaveEditor();
    return;
  }
  uni.showActionSheet({
    title: "项目有未保存修改",
    itemList: ["保存草稿后退出", "放弃本地修改", "继续编辑"],
    success: (result) => {
      if (result.tapIndex === 0) void saveDraft(true);
      if (result.tapIndex === 1) {
        recoveryStorage.clearProject();
        leaveEditor();
      }
    },
  });
}

watch(
  draft,
  () => {
    if (ready.value && dirty.value) recoveryStorage.writeProject(draft);
  },
  { deep: true },
);

onBackPress(() => {
  if (allowLeave || !dirty.value) return false;
  requestLeave();
  return true;
});

onLoad(loadProject);
</script>

<style scoped>
.form-loading {
  padding: 32rpx 0;
}

.form-loading__row {
  margin-top: 34rpx;
}

.form-loading__label,
.form-loading__control {
  border-radius: 6rpx;
  background: #e3eae6;
}

.form-loading__label {
  width: 28%;
  height: 24rpx;
}

.form-loading__control {
  height: 88rpx;
  margin-top: 14rpx;
}

.form-status {
  margin-top: 24rpx;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.draft-version,
.role-count {
  flex: 0 0 auto;
  color: #74817b;
  font-size: 21rpx;
  font-weight: 700;
}

.field-grid {
  display: grid;
  gap: 18rpx;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-grid__item {
  min-width: 0;
}

.picker-control {
  display: flex;
  height: 88rpx;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 0 24rpx;
  border: 1rpx solid #cfd9d3;
  border-radius: 8rpx;
  background: #ffffff;
  color: #17231e;
  font-size: 27rpx;
}

.text-area--project {
  min-height: 240rpx;
}

.field-counter {
  display: flex;
  min-height: 36rpx;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-top: 8rpx;
  color: #87948e;
  font-size: 21rpx;
}

.field-counter .field-error {
  margin-top: 0;
}

.role-section {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.role-editor {
  padding: 26rpx;
  border: 1rpx solid #d7e0dc;
  border-radius: 8rpx;
  background: #ffffff;
}

.role-editor__header {
  display: flex;
  min-height: 62rpx;
  align-items: center;
  gap: 14rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid #e0e7e3;
}

.role-editor__number {
  display: flex;
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
  align-items: center;
  justify-content: center;
  border-radius: 5rpx;
  background: #173d32;
  color: #ffffff;
  font-size: 21rpx;
  font-weight: 800;
}

.role-editor__title {
  color: #26352f;
  font-size: 27rpx;
  font-weight: 800;
}

.role-editor__remove {
  display: flex;
  width: 68rpx;
  height: 68rpx;
  flex: 0 0 68rpx;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  border: 1rpx solid #e5c3bd;
  border-radius: 8rpx;
  background: #fff8f6;
  line-height: 1;
}

.role-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  margin-top: 28rpx;
  padding-top: 22rpx;
  border-top: 1rpx solid #e0e7e3;
}

.role-status__title,
.role-status__copy {
  display: block;
}

.role-status__title {
  color: #2b3933;
  font-size: 25rpx;
  font-weight: 700;
}

.role-status__copy {
  margin-top: 6rpx;
  color: #74817b;
  font-size: 21rpx;
  line-height: 1.45;
}

.add-role-button {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
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
  line-height: 1.45;
  text-align: center;
}

@media (max-width: 360px) {
  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
