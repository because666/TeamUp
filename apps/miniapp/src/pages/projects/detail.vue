<template>
  <view class="page-shell page-shell--task">
    <view class="page-content">
      <BrandHeader caption="项目详情" back />
      <FixtureBanner />

      <view v-if="loading" class="detail-loading">
        <view class="detail-loading__line detail-loading__line--short" />
        <view class="detail-loading__line detail-loading__line--title" />
        <view class="detail-loading__block" />
      </view>

      <view v-else-if="errorView" class="section">
        <StatusPanel
          :title="errorView.title"
          :description="errorDescription"
          tone="error"
          action-label="重试"
          @action="loadProject"
        />
      </view>

      <template v-else>
        <view class="project-overview surface">
          <view class="project-overview__topline">
            <text class="project-overview__direction">{{ project.direction }}</text>
            <text class="project-overview__stage">{{ stageLabel }}</text>
          </view>
          <text class="project-overview__title">{{ project.title }}</text>
          <text class="project-overview__description">{{ project.description }}</text>
          <view class="project-overview__facts">
            <view>
              <text class="project-overview__fact-label">适配赛事</text>
              <text class="project-overview__fact-value">{{ project.competition || "未指定" }}</text>
            </view>
            <view>
              <text class="project-overview__fact-label">现有团队</text>
              <text class="project-overview__fact-value">{{ project.teamInfo || "暂未填写" }}</text>
            </view>
          </view>
        </view>

        <view class="section role-section">
          <view class="role-section__heading">
            <view>
              <text class="section-title">开放岗位</text>
              <text class="section-copy">{{ openRoles.length }} 个岗位正在招募</text>
            </view>
          </view>

          <StatusPanel
            v-if="openRoles.length === 0"
            title="当前没有开放岗位"
            description="项目仍可查看，岗位状态以项目方后续更新为准。"
          />

          <view v-else class="role-list">
            <view v-for="role in openRoles" :key="role.id" class="role-item surface">
              <view class="role-item__heading">
                <text class="role-item__name">{{ role.name }}</text>
                <text class="role-item__headcount">招募 {{ role.headcount }} 人</text>
              </view>
              <text v-if="role.description" class="role-item__description">{{ role.description }}</text>
              <view class="role-item__skills">
                <text v-for="skill in role.skills" :key="skill" class="role-item__skill">{{ skill }}</text>
              </view>
              <view class="role-item__time">
                <uni-icons type="calendar" size="17" color="#607069" />
                <text>每周约 {{ role.hoursPerWeek }} 小时</text>
              </view>
              <button
                class="secondary-button role-item__contact"
                :disabled="contacting || contactStatus(role.id) === 'PENDING' || contactStatus(role.id) === 'ACCEPTED'"
                @click="contactOrganizer(role.id)"
              >
                <uni-icons type="personadd" size="19" :color="contactStatus(role.id) ? '#74817b' : '#12664f'" />
                <text>{{ contactButtonLabel(role.id) }}</text>
              </button>
              <view
                v-if="contactRoleId === role.id && contactFeedback"
                class="role-item__feedback"
                :class="{ 'role-item__feedback--error': contactError }"
              >
                <uni-icons
                  :type="contactError ? 'info' : 'checkmarkempty'"
                  size="16"
                  :color="contactError ? '#a5372a' : '#12664f'"
                />
                <text>{{ contactFeedback }}</text>
              </view>
            </view>
          </view>
        </view>
      </template>
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
import { AppServiceError } from "@/services/runtime";
import { openPage, routes } from "@/utils/navigation";

const loading = ref(true);
const projectId = ref("");
const project = ref<ProjectDraft>(emptyProjectDraft());
const errorView = ref<ErrorPresentation | null>(null);
const contacting = ref(false);
const contactStatusByRole = ref<Record<string, "PENDING" | "ACCEPTED">>({});
const contactRoleId = ref("");
const contactFeedback = ref("");
const contactError = ref(false);

const stageLabels: Record<string, string> = {
  IDEA: "方案设计",
  VALIDATION: "需求验证",
  PROTOTYPE: "原型验证",
  DEVELOPMENT: "开发中",
};

const stageLabel = computed(() => stageLabels[project.value.stage] || project.value.stage);
const openRoles = computed(() => project.value.roles.filter((role) => role.status === "OPEN"));
const errorDescription = computed(() => {
  if (!errorView.value) return "";
  return errorView.value.requestId === "local_request"
    ? errorView.value.description
    : `${errorView.value.description} 参考号：${errorView.value.requestId}`;
});

function contactStatus(roleId: string): "PENDING" | "ACCEPTED" | "" {
  return contactStatusByRole.value[roleId] || "";
}

function contactButtonLabel(roleId: string): string {
  if (contacting.value && contactRoleId.value === roleId) return "正在提交申请...";
  if (contactStatus(roleId) === "ACCEPTED") return "已交换联系方式";
  if (contactStatus(roleId) === "PENDING") return "已提交交换申请";
  return "申请交换联系方式";
}

async function contactOrganizer(roleId: string): Promise<void> {
  if (contacting.value || contactStatus(roleId)) return;
  contacting.value = true;
  contactRoleId.value = roleId;
  contactFeedback.value = "";
  contactError.value = false;
  try {
    const response = await repository.createContactExchangeRequest(project.value.id, roleId);
    contactStatusByRole.value[roleId] = response.data.status === "ACCEPTED" ? "ACCEPTED" : "PENDING";
    contactFeedback.value = response.data.status === "ACCEPTED"
      ? "双方已同意交换，请到“联系”查看对方方式。"
      : "申请已发出，对方同意后才能查看联系方式。";
  } catch (error) {
    const presentation = presentError(error);
    contactError.value = true;
    const detail = `${presentation.title}：${presentation.description}`;
    contactFeedback.value = presentation.requestId === "local_request"
      ? detail
      : `${detail} 参考号：${presentation.requestId}`;
    if (error instanceof AppServiceError && error.code === "CONTACT_CARD_REQUIRED") {
      openPage(routes.contactSettings);
    }
  } finally {
    contacting.value = false;
  }
}

async function loadProject(): Promise<void> {
  if (!projectId.value) {
    loading.value = false;
    errorView.value = {
      kind: "validation_error",
      title: "项目地址无效",
      description: "请返回发现页重新选择项目。",
      requestId: "local_request",
    };
    return;
  }

  loading.value = true;
  errorView.value = null;
  try {
    project.value = (await repository.getProjectById(projectId.value)).data;
  } catch (error) {
    errorView.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

onLoad((query) => {
  projectId.value = typeof query?.id === "string" ? query.id : "";
  void loadProject();
});
</script>

<style scoped>
.detail-loading {
  padding: 72rpx 0;
}

.detail-loading__line,
.detail-loading__block {
  border-radius: 6rpx;
  background: #e3eae6;
}

.detail-loading__line {
  height: 24rpx;
  margin-top: 18rpx;
}

.detail-loading__line--short {
  width: 30%;
}

.detail-loading__line--title {
  width: 68%;
  height: 36rpx;
}

.detail-loading__block {
  height: 220rpx;
  margin-top: 34rpx;
}

.project-overview {
  margin-top: 30rpx;
  padding: 32rpx;
}

.project-overview__topline,
.role-item__heading,
.role-item__time {
  display: flex;
  align-items: center;
}

.project-overview__topline,
.role-item__heading {
  justify-content: space-between;
  gap: 18rpx;
}

.project-overview__direction,
.project-overview__stage {
  color: #607069;
  font-size: 22rpx;
  font-weight: 700;
}

.project-overview__title {
  display: block;
  margin-top: 24rpx;
  color: #17231e;
  font-size: 40rpx;
  font-weight: 800;
  line-height: 1.35;
}

.project-overview__description {
  display: block;
  margin-top: 16rpx;
  color: #53625b;
  font-size: 25rpx;
  line-height: 1.65;
}

.project-overview__facts {
  display: grid;
  gap: 24rpx;
  margin-top: 30rpx;
  padding-top: 26rpx;
  border-top: 1rpx solid #e0e7e3;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.project-overview__facts > view {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 8rpx;
}

.project-overview__fact-label {
  color: #7a8781;
  font-size: 20rpx;
}

.project-overview__fact-value {
  color: #2c3c35;
  font-size: 23rpx;
  line-height: 1.5;
}

.role-section__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 24rpx;
}

.role-item {
  padding: 26rpx;
}

.role-item__name {
  color: #17231e;
  font-size: 29rpx;
  font-weight: 800;
}

.role-item__headcount {
  flex: 0 0 auto;
  color: #12664f;
  font-size: 21rpx;
  font-weight: 700;
}

.role-item__description {
  display: block;
  margin-top: 12rpx;
  color: #5d6b65;
  font-size: 23rpx;
  line-height: 1.55;
}

.role-item__skills {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.role-item__skill {
  padding: 8rpx 14rpx;
  border-radius: 6rpx;
  background: #e9f2ed;
  color: #12664f;
  font-size: 20rpx;
  font-weight: 700;
}

.role-item__time {
  gap: 8rpx;
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #e4eae7;
  color: #607069;
  font-size: 21rpx;
}

.role-item__contact {
  width: 100%;
  margin-top: 20rpx;
}

.role-item__contact[disabled] {
  border-color: #d5ded9;
  background: #eef2f0;
  color: #74817b;
}

.role-item__feedback {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  margin-top: 14rpx;
  color: #12664f;
  font-size: 21rpx;
  line-height: 1.5;
}

.role-item__feedback--error {
  color: #a5372a;
}

@media (max-width: 360px) {
  .project-overview__facts {
    grid-template-columns: 1fr;
  }
}
</style>
