<template>
  <view class="page-shell">
    <view class="page-content">
      <BrandHeader title="我的工作台" summary="管理能力名片、项目草稿和发布状态。" />
      <FixtureBanner />

      <view v-if="loading" class="workspace-loading">
        <view class="skeleton-line skeleton-line--wide" />
        <view class="skeleton-line" />
        <view class="skeleton-block" />
      </view>

      <view v-else-if="errorView" class="section">
        <StatusPanel
          :title="errorView.title"
          :description="errorView.description"
          tone="error"
          action-label="重试"
          @action="loadWorkspace"
        />
      </view>

      <template v-else>
        <view class="profile-strip">
          <view class="profile-strip__avatar">
            <text>{{ profileInitial }}</text>
          </view>
          <view class="profile-strip__body">
            <text class="profile-strip__name">{{ profile.nickname || "待完善能力名片" }}</text>
            <text class="profile-strip__meta">{{ profileMeta }}</text>
          </view>
          <view class="profile-strip__completion">
            <text class="profile-strip__score">{{ completion }}%</text>
            <view class="profile-strip__track">
              <view class="profile-strip__progress" :style="{ width: `${completion}%` }" />
            </view>
          </view>
        </view>

        <view class="section">
          <view class="section-heading">
            <view>
              <text class="section-title">能力名片</text>
              <text class="section-copy">{{ visibilityLabel }}</text>
            </view>
            <button class="icon-command" aria-label="编辑能力名片" @click="openPage(routes.profileEdit)">
              <uni-icons type="compose" size="20" color="#12664f" />
            </button>
          </view>
          <view class="skill-row">
            <text v-for="skill in profile.skills" :key="skill" class="skill-row__item">{{ skill }}</text>
            <text v-if="profile.skills.length === 0" class="skill-row__empty">尚未填写技能</text>
          </view>
        </view>

        <view class="section">
          <view class="section-heading">
            <view>
              <text class="section-title">我的项目</text>
              <text class="section-copy">{{ projectSummary }}</text>
            </view>
            <button class="icon-command" aria-label="进入我的项目" @click="openPage(routes.projectList)">
              <uni-icons type="right" size="20" color="#12664f" />
            </button>
          </view>
          <button class="primary-button workspace-command" @click="openPage(routes.projectEdit)">
            <uni-icons type="plusempty" size="20" color="#ffffff" />
            <text>{{ project.id ? "继续管理项目" : "创建项目草稿" }}</text>
          </button>
        </view>

        <view class="section workspace-links">
          <button class="workspace-link" @click="openPage(routes.contactSettings)">
            <uni-icons type="locked" size="20" color="#607069" />
            <text>联系方式</text>
            <uni-icons class="workspace-link__arrow" type="right" size="18" color="#74817b" />
          </button>
          <button class="workspace-link workspace-link--secondary">
            <uni-icons type="locked" size="20" color="#607069" />
            <text>账户与隐私</text>
            <text class="workspace-link__pending">待后续任务</text>
          </button>
        </view>
      </template>
    </view>
    <BottomNav active="me" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import BottomNav from "@/components/BottomNav.vue";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import { emptyProfileDraft, emptyProjectDraft, type ProfileDraft, type ProjectDraft } from "@/domain/models";
import { validateProfile } from "@/domain/validation";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { openPage, routes } from "@/utils/navigation";

const loading = ref(true);
const profile = ref<ProfileDraft>(emptyProfileDraft());
const project = ref<ProjectDraft>(emptyProjectDraft());
const errorView = ref<ErrorPresentation | null>(null);

const requiredFieldCount = 7;
const completion = computed(() => {
  const missing = Object.keys(validateProfile(profile.value)).length;
  return Math.max(0, Math.round(((requiredFieldCount - Math.min(missing, requiredFieldCount)) / requiredFieldCount) * 100));
});
const profileInitial = computed(() => profile.value.nickname.trim().slice(0, 1) || "我");
const profileMeta = computed(() => {
  const parts = [profile.value.school, profile.value.major].filter(Boolean);
  return parts.length ? parts.join(" · ") : "填写学校、专业和技能";
});
const visibilityLabel = computed(() =>
  profile.value.visibility ? "已公开到人才大厅" : "仅自己可见，联系方式不会公开",
);
const projectSummary = computed(() => {
  if (!project.value.id) return "还没有项目草稿";
  if (project.value.status === "PUBLISHED") return `已发布：${project.value.title}`;
  return `草稿：${project.value.title || "未命名项目"}`;
});

async function loadWorkspace(): Promise<void> {
  loading.value = true;
  errorView.value = null;
  try {
    const [profileResponse, projectResponse] = await Promise.all([
      repository.getProfile(),
      repository.getProject(),
    ]);
    profile.value = profileResponse.data;
    project.value = projectResponse.data;
  } catch (error) {
    errorView.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

onShow(loadWorkspace);
</script>

<style scoped>
.workspace-loading {
  padding: 44rpx 0;
}

.skeleton-line,
.skeleton-block {
  border-radius: 6rpx;
  background: #e4ebe7;
}

.skeleton-line {
  width: 44%;
  height: 26rpx;
  margin-top: 18rpx;
}

.skeleton-line--wide {
  width: 72%;
}

.skeleton-block {
  height: 180rpx;
  margin-top: 34rpx;
}

.profile-strip {
  display: flex;
  min-height: 164rpx;
  align-items: center;
  gap: 22rpx;
  margin-top: 32rpx;
  padding: 26rpx;
  border: 1rpx solid #d8e2dd;
  border-radius: 8rpx;
  background: #ffffff;
}

.profile-strip__avatar {
  display: flex;
  width: 84rpx;
  height: 84rpx;
  flex: 0 0 84rpx;
  align-items: center;
  justify-content: center;
  border-radius: 8rpx;
  background: #173d32;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 800;
}

.profile-strip__body {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 7rpx;
}

.profile-strip__name {
  overflow: hidden;
  color: #17231e;
  font-size: 31rpx;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-strip__meta,
.skill-row__empty {
  color: #74817b;
  font-size: 22rpx;
}

.profile-strip__completion {
  display: flex;
  width: 92rpx;
  flex: 0 0 92rpx;
  align-items: flex-end;
  flex-direction: column;
  gap: 10rpx;
}

.profile-strip__score {
  color: #12664f;
  font-size: 24rpx;
  font-weight: 800;
}

.profile-strip__track {
  width: 92rpx;
  height: 8rpx;
  overflow: hidden;
  border-radius: 8rpx;
  background: #dce9e2;
}

.profile-strip__progress {
  height: 100%;
  border-radius: inherit;
  background: #12664f;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.icon-command {
  display: flex;
  width: 76rpx;
  height: 76rpx;
  flex: 0 0 76rpx;
  align-items: center;
  justify-content: center;
  margin: 0 0 0 auto;
  border: 1rpx solid #bfd0c8;
  border-radius: 8rpx;
  background: #ffffff;
  line-height: 1;
}

.icon-command:active {
  background: #eaf3ef;
}

.skill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 22rpx;
}

.skill-row__item {
  padding: 10rpx 16rpx;
  border-radius: 6rpx;
  background: #e9f2ed;
  color: #12664f;
  font-size: 21rpx;
  font-weight: 700;
}

.workspace-command {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  margin-top: 26rpx;
}

.workspace-links {
  padding-bottom: 12rpx;
}

.workspace-link {
  display: flex;
  width: 100%;
  min-height: 92rpx;
  align-items: center;
  gap: 16rpx;
  padding: 0 22rpx;
  border: 1rpx solid #d9e3de;
  border-radius: 8rpx;
  background: #ffffff;
  color: #435149;
  font-size: 25rpx;
  text-align: left;
}

.workspace-link__pending {
  margin-left: auto;
  color: #8a9690;
  font-size: 21rpx;
}

.workspace-link__arrow {
  margin-left: auto;
}

.workspace-link--secondary {
  margin-top: 12rpx;
}
</style>
