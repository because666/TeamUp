<template>
  <view class="page-shell page-shell--task">
    <view class="page-content">
      <BrandHeader
        title="能力名片"
        summary="只填写协作真正需要的信息，是否公开由你决定。"
        caption="建立协作资料"
        back
        manual-back
        @back="requestLeave"
      />
      <ProgressRail :current="2" />
      <FixtureBanner />

      <view v-if="loading" class="form-loading">
        <view v-for="index in 4" :key="index" class="form-loading__row">
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

      <form v-else @submit.prevent="saveProfile">
        <view v-if="submitError" class="form-status">
          <StatusPanel
            :title="submitError.title"
            :description="errorDescription(submitError)"
            :tone="submitError.kind === 'conflict' ? 'warning' : 'error'"
            :action-label="submitError.kind === 'conflict' ? '重新加载' : '重试保存'"
            @action="submitError.kind === 'conflict' ? loadProfile() : saveProfile()"
          />
        </view>

        <view v-if="Object.keys(errors).length" class="form-status">
          <StatusPanel
            title="请完成标记的信息"
            :description="`共 ${Object.keys(errors).length} 项需要确认，已保留你的其他输入。`"
            tone="warning"
          />
        </view>

        <view class="section">
          <text class="section-title">基本信息</text>
          <text class="section-copy">用于项目成员快速了解你的学习背景。</text>

          <view class="field">
            <text class="field-label">昵称 *</text>
            <input
              v-model="draft.nickname"
              class="text-input"
              maxlength="24"
              placeholder="例如：林同学"
            />
            <text v-if="errors['PF-NICKNAME']" class="field-error">{{ errors["PF-NICKNAME"] }}</text>
          </view>

          <view class="field field-grid">
            <view class="field-grid__item">
              <text class="field-label">院校 *</text>
              <input v-model="draft.school" class="text-input" maxlength="40" placeholder="你的学校" />
              <text v-if="errors['PF-SCHOOL']" class="field-error">{{ errors["PF-SCHOOL"] }}</text>
            </view>
            <view class="field-grid__item">
              <text class="field-label">专业 *</text>
              <input v-model="draft.major" class="text-input" maxlength="40" placeholder="你的专业" />
              <text v-if="errors['PF-MAJOR']" class="field-error">{{ errors["PF-MAJOR"] }}</text>
            </view>
          </view>

          <view class="field">
            <text class="field-label">年级 *</text>
            <picker :range="gradeOptions" :value="gradeIndex" @change="selectGrade">
              <view class="picker-control" :class="{ 'picker-control--placeholder': !draft.grade }">
                <text>{{ draft.grade || "选择年级" }}</text>
                <uni-icons type="down" size="17" color="#74817b" />
              </view>
            </picker>
            <text v-if="errors['PF-GRADE']" class="field-error">{{ errors["PF-GRADE"] }}</text>
          </view>
        </view>

        <view class="section">
          <text class="section-title">能力与合作</text>
          <text class="section-copy">结构化标签只用于发现和后续可解释匹配。</text>

          <view class="field">
            <text class="field-label">技能 *</text>
            <TagSelector v-model="draft.skills" :options="skillOptions" />
            <text v-if="errors['PF-SKILLS']" class="field-error">{{ errors["PF-SKILLS"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">合作场景 *</text>
            <TagSelector v-model="draft.collaborationScenarios" :options="scenarioOptions" />
            <text v-if="errors['PF-SCENARIO']" class="field-error">{{ errors["PF-SCENARIO"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">角色偏好 *</text>
            <view class="choice-grid">
              <button
                v-for="option in roleOptions"
                :key="option.value"
                class="choice-grid__item"
                :class="{ 'choice-grid__item--active': draft.rolePreference === option.value }"
                @click="draft.rolePreference = option.value"
              >
                {{ option.label }}
              </button>
            </view>
            <text v-if="errors['PF-ROLE-PREF']" class="field-error">{{ errors["PF-ROLE-PREF"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">每周可投入时间 *</text>
            <NumberStepper v-model="draft.hoursPerWeek" :min="1" :max="40" unit="小时" />
            <text v-if="errors['PF-HOURS']" class="field-error">{{ errors["PF-HOURS"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">个人简介</text>
            <textarea
              v-model="draft.bio"
              class="text-area"
              maxlength="240"
              placeholder="写下你擅长什么，以及希望怎样协作"
            />
            <view class="field-counter">
              <text v-if="errors['PF-BIO']" class="field-error">{{ errors["PF-BIO"] }}</text>
              <text>{{ draft.bio.length }}/240</text>
            </view>
          </view>
        </view>

        <view class="section">
          <view class="visibility-row surface">
            <view class="visibility-row__body">
              <text class="visibility-row__title">进入人才大厅</text>
              <text class="visibility-row__copy">默认关闭；开启后公开昵称、院校、专业、技能与简介。</text>
            </view>
            <switch
              :checked="draft.visibility"
              color="#12664f"
              @change="changeVisibility"
            />
          </view>
        </view>

        <view class="task-actions">
          <button class="primary-button" :disabled="saving" @click="saveProfile">
            {{ saving ? "正在保存…" : "保存能力名片" }}
          </button>
          <text class="task-actions__meta">
            {{ dirty ? "有未保存修改" : `已保存版本 ${draft.version}` }}
          </text>
        </view>
      </form>
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
import { emptyProfileDraft, type FieldErrors, type ProfileDraft } from "@/domain/models";
import { validateProfile } from "@/domain/validation";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { recoveryStorage } from "@/services/storage";
import { openMain, replacePage, routes } from "@/utils/navigation";

const gradeOptions = ["大一", "大二", "大三", "大四", "硕士", "博士", "其他"];
const skillOptions = ["产品设计", "UI 设计", "Vue", "Java", "Python", "数据分析", "内容策划", "运营"];
const scenarioOptions = ["竞赛", "科研", "创新创业", "课程项目"];
const roleOptions: Array<{ label: string; value: ProfileDraft["rolePreference"] }> = [
  { label: "愿意带队", value: "LEADER" },
  { label: "加入团队", value: "MEMBER" },
  { label: "均可", value: "FLEXIBLE" },
];

const draft = reactive<ProfileDraft>(emptyProfileDraft());
const errors = ref<FieldErrors>({});
const loading = ref(true);
const saving = ref(false);
const ready = ref(false);
const confirmedSnapshot = ref("");
const loadError = ref<ErrorPresentation | null>(null);
const submitError = ref<ErrorPresentation | null>(null);
let allowLeave = false;

const gradeIndex = computed(() => Math.max(0, gradeOptions.indexOf(draft.grade)));
const dirty = computed(() => ready.value && JSON.stringify(draft) !== confirmedSnapshot.value);

function replaceDraft(value: ProfileDraft): void {
  Object.assign(draft, JSON.parse(JSON.stringify(value)) as ProfileDraft);
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

async function loadProfile(): Promise<void> {
  loading.value = true;
  ready.value = false;
  loadError.value = null;
  submitError.value = null;
  try {
    const response = await repository.getProfile();
    const serverDraft = response.data;
    replaceDraft(serverDraft);
    confirmedSnapshot.value = JSON.stringify(serverDraft);

    const recovery = recoveryStorage.readProfile();
    if (recovery && JSON.stringify(recovery) !== confirmedSnapshot.value) {
      const restore = await confirmDialog(
        "发现未保存内容",
        "上次编辑可能被中断，是否恢复保存在本机的能力名片草稿？",
        "恢复草稿",
        "使用已保存版本",
      );
      if (restore) replaceDraft(recovery);
      else recoveryStorage.clearProfile();
    }
    ready.value = true;
  } catch (error) {
    loadError.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

function selectGrade(event: { detail: { value: string | number } }): void {
  draft.grade = gradeOptions[Number(event.detail.value)] || "";
}

async function changeVisibility(event: Event): Promise<void> {
  const checked = (event as Event & { detail: { value: boolean } }).detail.value;
  if (!checked) {
    draft.visibility = false;
    return;
  }
  draft.visibility = await confirmDialog(
    "确认公开能力名片",
    "开启后会公开昵称、院校、专业、技能和简介；联系方式不会公开。",
    "确认公开",
    "保持关闭",
  );
}

async function saveProfile(): Promise<void> {
  if (saving.value) return;
  errors.value = validateProfile(draft);
  submitError.value = null;
  if (Object.keys(errors.value).length) {
    uni.pageScrollTo({ scrollTop: 0, duration: 240 });
    return;
  }

  saving.value = true;
  try {
    const response = await repository.saveProfile(draft);
    replaceDraft(response.data);
    confirmedSnapshot.value = JSON.stringify(response.data);
    recoveryStorage.clearProfile();
    errors.value = {};
    allowLeave = true;
    uni.showToast({ title: "能力名片已保存", icon: "success" });
    if (getCurrentPages().length > 1) uni.navigateBack();
    else openMain("me");
  } catch (error) {
    submitError.value = presentError(error);
  } finally {
    saving.value = false;
  }
}

function handleLoadError(): void {
  if (loadError.value?.kind === "unauthenticated") replacePage(routes.login);
  else void loadProfile();
}

function leaveProfile(): void {
  allowLeave = true;
  if (getCurrentPages().length > 1) uni.navigateBack();
  else openMain("me");
}

function requestLeave(): void {
  if (allowLeave || !dirty.value) {
    leaveProfile();
    return;
  }
  void confirmDialog(
    "放弃未保存修改？",
    "本次修改尚未保存，放弃后会清除本机恢复草稿。",
    "放弃修改",
    "继续编辑",
  ).then((discard) => {
    if (!discard) return;
    recoveryStorage.clearProfile();
    leaveProfile();
  });
}

watch(
  draft,
  () => {
    if (ready.value && dirty.value) recoveryStorage.writeProfile(draft);
  },
  { deep: true },
);

onBackPress(() => {
  if (allowLeave || !dirty.value) return false;
  requestLeave();
  return true;
});

onLoad(loadProfile);
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

.picker-control--placeholder {
  color: #87948e;
}

.choice-grid {
  display: grid;
  gap: 12rpx;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.choice-grid__item {
  min-width: 0;
  min-height: 78rpx;
  padding: 0 10rpx;
  border: 1rpx solid #cbd6d0;
  border-radius: 6rpx;
  background: #ffffff;
  color: #435149;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 78rpx;
}

.choice-grid__item--active {
  border-color: #12664f;
  background: #eaf3ef;
  color: #12664f;
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

.visibility-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 26rpx;
}

.visibility-row__body {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 8rpx;
}

.visibility-row__title {
  color: #26352f;
  font-size: 27rpx;
  font-weight: 700;
}

.visibility-row__copy {
  color: #66746e;
  font-size: 22rpx;
  line-height: 1.55;
}

.task-actions {
  padding: 32rpx 0 12rpx;
  border-top: 1rpx solid #dce4df;
}

.task-actions .primary-button {
  width: 100%;
}

.task-actions__meta {
  display: block;
  margin-top: 14rpx;
  color: #74817b;
  font-size: 21rpx;
  text-align: center;
}

@media (max-width: 360px) {
  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
