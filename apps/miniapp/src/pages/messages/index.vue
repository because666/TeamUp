<template>
  <view class="page-shell">
    <view class="page-content">
      <BrandHeader title="联系" summary="处理联系方式交换和项目邀请。">
        <template #action>
          <button class="contact-settings" aria-label="设置联系方式" @click="openPage(routes.contactSettings)">
            <uni-icons type="gear" size="21" color="#12664f" />
          </button>
        </template>
      </BrandHeader>
      <FixtureBanner />

      <view class="contact-tabs contact-tabs--primary">
        <button
          class="contact-tabs__item"
          :class="{ 'contact-tabs__item--active': activeSection === 'EXCHANGE' }"
          @click="selectSection('EXCHANGE')"
        >
          联系方式
        </button>
        <button
          class="contact-tabs__item"
          :class="{ 'contact-tabs__item--active': activeSection === 'INVITATIONS' }"
          @click="selectSection('INVITATIONS')"
        >
          项目邀请
        </button>
      </view>

      <view class="box-tabs" aria-label="列表方向">
        <button
          class="box-tabs__item"
          :class="{ 'box-tabs__item--active': activeBox === 'RECEIVED' }"
          @click="selectBox('RECEIVED')"
        >
          收到
        </button>
        <button
          class="box-tabs__item"
          :class="{ 'box-tabs__item--active': activeBox === 'SENT' }"
          @click="selectBox('SENT')"
        >
          发出
        </button>
      </view>

      <view v-if="loading" class="contact-list contact-list--loading">
        <view v-for="index in 2" :key="index" class="contact-skeleton surface">
          <view class="contact-skeleton__line contact-skeleton__line--short" />
          <view class="contact-skeleton__line" />
          <view class="contact-skeleton__button" />
        </view>
      </view>

      <view v-else-if="loadError" class="section">
        <StatusPanel
          :title="loadError.title"
          :description="loadError.description"
          tone="error"
          action-label="重试"
          @action="loadItems"
        />
      </view>

      <view v-else-if="visibleItems.length === 0" class="section">
        <StatusPanel
          :title="emptyTitle"
          :description="emptyDescription"
        />
      </view>

      <view v-else-if="activeSection === 'EXCHANGE'" class="contact-list">
        <view v-for="item in requests" :key="item.id" class="contact-request surface">
          <view class="contact-request__heading">
            <view class="contact-request__identity">
              <text class="contact-request__project">{{ item.projectTitle }}</text>
              <text class="contact-request__role">{{ item.roleName }} · {{ item.peerDisplayName }}</text>
            </view>
            <text class="contact-request__status" :class="`contact-request__status--${item.status.toLowerCase()}`">
              {{ contactStatusLabel(item) }}
            </text>
          </view>
          <text class="contact-request__time">{{ formatTime(item.createdAt) }}</text>

          <view v-if="item.status === 'ACCEPTED' && item.peerContactCard" class="contact-methods">
            <view v-for="method in item.peerContactCard.methods" :key="method.type" class="contact-method">
              <view class="contact-method__body">
                <text class="contact-method__label">{{ methodLabel(method.type) }}</text>
                <text class="contact-method__value" selectable>{{ method.value }}</text>
              </view>
              <button class="contact-method__copy" :aria-label="`复制${methodLabel(method.type)}`" @click="copyMethod(method.value)">
                复制
              </button>
            </view>
          </view>

          <view v-else-if="item.status === 'ACCEPTED'" class="contact-request__notice">
            <uni-icons type="info" size="17" color="#a5372a" />
            <text>对方联系方式暂不可用，请刷新后重试。</text>
          </view>

          <view v-if="item.status === 'PENDING' && item.box === 'RECEIVED'" class="contact-request__actions">
            <button class="secondary-button" :disabled="actionBusyId === item.id" @click="act(item, 'reject')">
              拒绝
            </button>
            <button class="primary-button" :disabled="actionBusyId === item.id" @click="act(item, 'accept')">
              {{ actionBusyId === item.id ? "处理中..." : "同意交换" }}
            </button>
          </view>

          <button
            v-else-if="item.status === 'PENDING' && item.box === 'SENT'"
            class="text-button contact-request__cancel"
            :disabled="actionBusyId === item.id"
            @click="act(item, 'cancel')"
          >
            {{ actionBusyId === item.id ? "正在取消..." : "取消申请" }}
          </button>

          <view v-if="actionFeedback[item.id]" class="contact-request__notice contact-request__notice--error">
            <uni-icons type="info" size="17" color="#a5372a" />
            <text>{{ actionFeedback[item.id] }}</text>
          </view>
        </view>
      </view>

      <view v-else class="contact-list">
        <view v-for="item in invitations" :key="item.id" class="contact-request surface">
          <view class="contact-request__heading">
            <view class="contact-request__identity">
              <text class="contact-request__project">{{ item.projectTitle }}</text>
              <text class="contact-request__role">{{ item.roleName }} · {{ item.peerDisplayName }}</text>
            </view>
            <text class="contact-request__status" :class="`contact-request__status--${item.status.toLowerCase()}`">
              {{ invitationStatusLabel(item) }}
            </text>
          </view>
          <text class="contact-request__time">{{ formatTime(item.createdAt) }}</text>
          <text v-if="item.status === 'PENDING'" class="invitation-expiry">
            {{ formatExpiry(item.expiresAt) }}前可处理
          </text>

          <view v-if="item.status === 'ACCEPTED'" class="contact-request__notice contact-request__notice--success">
            <uni-icons type="checkmarkempty" size="17" color="#12664f" />
            <text>{{ item.box === "RECEIVED" ? "你已加入该项目岗位。" : "对方已接受邀请并加入项目。" }}</text>
          </view>

          <view v-if="item.status === 'PENDING' && item.box === 'RECEIVED'" class="contact-request__actions">
            <button class="secondary-button" :disabled="actionBusyId === item.id" @click="actOnInvitation(item, 'reject')">
              拒绝
            </button>
            <button class="primary-button" :disabled="actionBusyId === item.id" @click="actOnInvitation(item, 'accept')">
              {{ actionBusyId === item.id ? "处理中..." : "接受邀请" }}
            </button>
          </view>

          <view v-if="actionFeedback[item.id]" class="contact-request__notice contact-request__notice--error">
            <uni-icons type="info" size="17" color="#a5372a" />
            <text>{{ actionFeedback[item.id] }}</text>
          </view>
        </view>
      </view>
    </view>
    <BottomNav active="messages" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import BottomNav from "@/components/BottomNav.vue";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import type {
  ContactExchangeBox,
  ContactExchangeRequest,
  ContactMethodType,
  ProjectInvitation,
  ProjectInvitationBox,
} from "@/domain/models";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";
import { AppServiceError } from "@/services/runtime";
import { openPage, routes } from "@/utils/navigation";

type ContactSection = "EXCHANGE" | "INVITATIONS";

const activeSection = ref<ContactSection>("EXCHANGE");
const activeBox = ref<ContactExchangeBox | ProjectInvitationBox>("RECEIVED");
const requests = ref<ContactExchangeRequest[]>([]);
const invitations = ref<ProjectInvitation[]>([]);
const loading = ref(true);
const loadError = ref<ErrorPresentation | null>(null);
const actionBusyId = ref("");
const actionFeedback = ref<Record<string, string>>({});

const visibleItems = computed(() => (
  activeSection.value === "EXCHANGE" ? requests.value : invitations.value
));
const emptyTitle = computed(() => {
  if (activeSection.value === "INVITATIONS") {
    return activeBox.value === "RECEIVED" ? "还没有收到项目邀请" : "还没有发出项目邀请";
  }
  return activeBox.value === "RECEIVED" ? "还没有收到交换申请" : "还没有发出交换申请";
});
const emptyDescription = computed(() => {
  if (activeSection.value === "INVITATIONS") {
    return activeBox.value === "RECEIVED"
      ? "项目方发出的岗位邀请会出现在这里。"
      : "你代表项目发出的岗位邀请会出现在这里。";
  }
  return activeBox.value === "RECEIVED"
    ? "新的联系方式交换申请会出现在这里。"
    : "可从项目详情的开放岗位发起申请。";
});

const methodLabels: Record<ContactMethodType, string> = {
  WECHAT: "微信号",
  QQ: "QQ",
  EMAIL: "邮箱",
};

function methodLabel(type: ContactMethodType): string {
  return methodLabels[type];
}

function contactStatusLabel(item: ContactExchangeRequest): string {
  if (item.status === "PENDING") return item.box === "RECEIVED" ? "待处理" : "等待对方";
  if (item.status === "ACCEPTED") return item.box === "RECEIVED" ? "已同意" : "对方已同意";
  if (item.status === "REJECTED") return item.box === "RECEIVED" ? "已拒绝" : "对方已拒绝";
  return item.box === "RECEIVED" ? "对方已取消" : "已取消";
}

function invitationStatusLabel(item: ProjectInvitation): string {
  if (item.status === "PENDING") return item.box === "RECEIVED" ? "待处理" : "等待对方";
  if (item.status === "ACCEPTED") return item.box === "RECEIVED" ? "已接受" : "对方已接受";
  if (item.status === "REJECTED") return item.box === "RECEIVED" ? "已拒绝" : "对方已拒绝";
  if (item.status === "EXPIRED") return "已过期";
  return "已取消";
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function formatExpiry(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "有效期内";
  return `${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

async function loadItems(): Promise<void> {
  loading.value = true;
  loadError.value = null;
  try {
    if (activeSection.value === "EXCHANGE") {
      requests.value = (
        await repository.listContactExchangeRequests(activeBox.value as ContactExchangeBox)
      ).data;
    } else {
      invitations.value = (
        await repository.listProjectInvitations(activeBox.value as ProjectInvitationBox)
      ).data;
    }
  } catch (error) {
    loadError.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

function selectSection(section: ContactSection): void {
  if (activeSection.value === section) return;
  activeSection.value = section;
  actionFeedback.value = {};
  void loadItems();
}

function selectBox(box: ContactExchangeBox | ProjectInvitationBox): void {
  if (activeBox.value === box) return;
  activeBox.value = box;
  actionFeedback.value = {};
  void loadItems();
}

async function actOnInvitation(
  item: ProjectInvitation,
  action: "accept" | "reject",
): Promise<void> {
  if (actionBusyId.value) return;
  actionBusyId.value = item.id;
  actionFeedback.value[item.id] = "";
  try {
    const updated = (await repository.actOnProjectInvitation(item.id, action)).data;
    const index = invitations.value.findIndex((invitation) => invitation.id === item.id);
    if (index >= 0) invitations.value[index] = { ...invitations.value[index], ...updated };
    if (action === "accept") uni.showToast({ title: "已加入项目", icon: "success" });
  } catch (error) {
    const presentation = presentError(error);
    actionFeedback.value[item.id] = `${presentation.title}：${presentation.description}`;
  } finally {
    actionBusyId.value = "";
  }
}

async function act(
  item: ContactExchangeRequest,
  action: "accept" | "reject" | "cancel",
): Promise<void> {
  if (actionBusyId.value) return;
  actionBusyId.value = item.id;
  actionFeedback.value[item.id] = "";
  try {
    const updated = (await repository.actOnContactExchangeRequest(item.id, action)).data;
    const index = requests.value.findIndex((request) => request.id === item.id);
    if (index >= 0) requests.value[index] = updated;
  } catch (error) {
    const presentation = presentError(error);
    actionFeedback.value[item.id] = `${presentation.title}：${presentation.description}`;
    if (error instanceof AppServiceError && error.code === "CONTACT_CARD_REQUIRED") {
      openPage(routes.contactSettings);
    }
  } finally {
    actionBusyId.value = "";
  }
}

function copyMethod(value: string): void {
  uni.setClipboardData({
    data: value,
    success: () => uni.showToast({ title: "已复制", icon: "success" }),
    fail: () => uni.showToast({ title: "复制失败", icon: "none" }),
  });
}

onShow(loadItems);
</script>

<style scoped>
.contact-settings {
  display: flex;
  width: 88rpx;
  height: 88rpx;
  flex: 0 0 88rpx;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  border: 1rpx solid #c8d5cf;
  border-radius: 8rpx;
  background: #ffffff;
  line-height: 1;
}

.contact-tabs {
  display: grid;
  gap: 8rpx;
  margin-top: 20rpx;
  padding: 8rpx;
  border: 1rpx solid #d9e3de;
  border-radius: 8rpx;
  background: #ffffff;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.contact-tabs--primary {
  margin-top: 20rpx;
}

.contact-tabs__item {
  display: flex;
  width: 100%;
  min-height: 88rpx;
  align-items: center;
  justify-content: center;
  border-radius: 6rpx;
  background: transparent;
  color: #74817b;
  font-size: 25rpx;
  font-weight: 700;
}

.contact-tabs__item--active {
  background: #e9f3ee;
  color: #12664f;
}

.box-tabs {
  display: flex;
  gap: 28rpx;
  margin-top: 18rpx;
  border-bottom: 1rpx solid #dce5e0;
}

.box-tabs__item {
  position: relative;
  min-width: 96rpx;
  min-height: 88rpx;
  padding: 0 8rpx;
  background: transparent;
  color: #74817b;
  font-size: 24rpx;
  font-weight: 700;
}

.box-tabs__item--active {
  color: #17231e;
}

.box-tabs__item--active::after {
  position: absolute;
  right: 8rpx;
  bottom: -1rpx;
  left: 8rpx;
  height: 4rpx;
  border-radius: 4rpx 4rpx 0 0;
  background: #12664f;
  content: "";
}

.contact-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 28rpx 0 12rpx;
}

.contact-request,
.contact-skeleton {
  padding: 26rpx;
}

.contact-request__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.contact-request__identity {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 7rpx;
}

.contact-request__project {
  color: #17231e;
  font-size: 28rpx;
  font-weight: 800;
  line-height: 1.4;
}

.contact-request__role,
.contact-request__time {
  color: #69776f;
  font-size: 22rpx;
  line-height: 1.5;
}

.contact-request__status {
  flex: 0 0 auto;
  padding: 8rpx 12rpx;
  border-radius: 6rpx;
  background: #edf2ef;
  color: #607069;
  font-size: 20rpx;
  font-weight: 700;
}

.contact-request__status--pending {
  background: #fff4d9;
  color: #8a5b13;
}

.contact-request__status--accepted {
  background: #e6f3ec;
  color: #12664f;
}

.contact-request__time {
  display: block;
  margin-top: 14rpx;
}

.contact-methods {
  margin-top: 22rpx;
  border-top: 1rpx solid #e1e8e4;
}

.contact-method {
  display: flex;
  min-height: 96rpx;
  align-items: center;
  gap: 18rpx;
  border-bottom: 1rpx solid #e7ece9;
}

.contact-method:last-child {
  border-bottom: 0;
}

.contact-method__body {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 5rpx;
}

.contact-method__label {
  color: #74817b;
  font-size: 20rpx;
}

.contact-method__value {
  overflow-wrap: anywhere;
  color: #24362f;
  font-size: 25rpx;
  line-height: 1.45;
}

.contact-method__copy {
  min-width: 88rpx;
  min-height: 88rpx;
  padding: 0 16rpx;
  border: 1rpx solid #bed0c7;
  border-radius: 6rpx;
  background: #ffffff;
  color: #12664f;
  font-size: 22rpx;
  font-weight: 700;
}

.contact-request__actions {
  display: grid;
  gap: 14rpx;
  margin-top: 22rpx;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
}

.contact-request__actions button {
  width: 100%;
}

.contact-request__cancel {
  width: 100%;
  margin-top: 12rpx;
}

.contact-request__notice {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  margin-top: 18rpx;
  color: #a5372a;
  font-size: 21rpx;
  line-height: 1.5;
}

.contact-request__notice--success {
  color: #12664f;
}

.invitation-expiry {
  display: block;
  margin-top: 8rpx;
  color: #8a5b13;
  font-size: 21rpx;
  line-height: 1.5;
}

.contact-skeleton__line,
.contact-skeleton__button {
  border-radius: 6rpx;
  background: #e3eae6;
}

.contact-skeleton__line {
  width: 72%;
  height: 24rpx;
  margin-top: 14rpx;
}

.contact-skeleton__line--short {
  width: 42%;
  margin-top: 0;
}

.contact-skeleton__button {
  height: 88rpx;
  margin-top: 28rpx;
}

@media (max-width: 360px) {
  .contact-request__actions {
    grid-template-columns: 1fr;
  }
}
</style>
