<template>
  <view class="page-shell page-shell--task login-page">
    <view class="page-content">
      <BrandHeader caption="高校项目协作" />
      <ProgressRail :current="1" />

      <view class="login-intro">
        <text class="login-intro__eyebrow">微信小程序</text>
        <text class="login-intro__title">找到认真做事的队友</text>
        <text class="login-intro__copy">
          用结构化能力名片和项目岗位，把组队需要的信息先说清楚。
        </text>
      </view>

      <view class="login-panel surface">
        <FixtureBanner />

        <view v-if="errorView" class="login-panel__status">
          <StatusPanel
            :title="errorView.title"
            :description="errorDescription"
            tone="error"
            action-label="重试"
            @action="submitLogin"
          />
        </view>

        <button class="consent-row" @click="consentAccepted = !consentAccepted">
          <view class="consent-box" :class="{ 'consent-box--checked': consentAccepted }">
            <uni-icons
              v-if="consentAccepted"
              type="checkmarkempty"
              size="14"
              color="#ffffff"
            />
          </view>
          <text class="consent-row__copy">我已阅读并同意下方说明</text>
        </button>

        <view class="policy-row">
          <button class="policy-link" @click="showPolicy('服务条款')">服务条款（待发布）</button>
          <text class="policy-row__dot">·</text>
          <button class="policy-link" @click="showPolicy('隐私政策')">隐私政策（待发布）</button>
        </view>

        <button
          class="primary-button login-button"
          :disabled="!consentAccepted || submitting"
          @click="submitLogin"
        >
          <uni-icons type="weixin" size="21" color="#ffffff" />
          <text>{{ submitting ? "正在建立会话…" : "使用微信继续" }}</text>
        </button>

        <text class="login-panel__notice">
          当前正式条款与隐私政策尚待发布；开发演示不会获取真实微信身份或签发平台凭证。
        </text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import ProgressRail from "@/components/ProgressRail.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import { repository } from "@/services/repository";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { routes, replacePage } from "@/utils/navigation";

const consentAccepted = ref(false);
const submitting = ref(false);
const errorView = ref<ErrorPresentation | null>(null);
const errorDescription = computed(() => {
  if (!errorView.value) return "";
  const request = errorView.value.requestId === "local_request"
    ? ""
    : `参考号：${errorView.value.requestId}`;
  return [errorView.value.description, request].filter(Boolean).join(" ");
});

function showPolicy(name: string): void {
  uni.showModal({
    title: `${name}尚待发布`,
    content: "当前仅用于前端开发演示，正式版本上线前必须补齐文本、版本号与生效日期并重新取得同意。",
    showCancel: false,
  });
}

async function submitLogin(): Promise<void> {
  if (!consentAccepted.value || submitting.value) return;
  submitting.value = true;
  errorView.value = null;
  try {
    const response = await repository.login(consentAccepted.value);
    replacePage(
      response.data.state === "AUTHENTICATED_PROFILE_INCOMPLETE"
        ? routes.profileEdit
        : routes.discover,
    );
  } catch (error) {
    errorView.value = presentError(error);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-page {
  background: #f4f7f5;
}

.login-intro {
  padding: 58rpx 0 42rpx;
}

.login-intro__eyebrow {
  display: block;
  color: #12664f;
  font-size: 23rpx;
  font-weight: 700;
}

.login-intro__title {
  display: block;
  max-width: 620rpx;
  margin-top: 14rpx;
  color: #17231e;
  font-size: 54rpx;
  font-weight: 800;
  line-height: 1.22;
}

.login-intro__copy {
  display: block;
  max-width: 640rpx;
  margin-top: 20rpx;
  color: #607069;
  font-size: 27rpx;
  line-height: 1.7;
}

.login-panel {
  padding: 30rpx;
}

.login-panel__status {
  margin-top: 24rpx;
}

.consent-row {
  display: flex;
  width: 100%;
  min-height: 88rpx;
  align-items: center;
  gap: 18rpx;
  margin-top: 26rpx;
  padding: 0;
  background: transparent;
  color: #2b3933;
  line-height: 1.45;
  text-align: left;
}

.consent-box {
  display: flex;
  width: 40rpx;
  height: 40rpx;
  flex: 0 0 40rpx;
  align-items: center;
  justify-content: center;
  border: 2rpx solid #aab8b1;
  border-radius: 5rpx;
  background: #ffffff;
}

.consent-box--checked {
  border-color: #12664f;
  background: #12664f;
}

.consent-row__copy {
  font-size: 25rpx;
}

.policy-row {
  display: flex;
  min-height: 72rpx;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
}

.policy-link {
  width: auto;
  min-height: 72rpx;
  padding: 0;
  background: transparent;
  color: #12664f;
  font-size: 24rpx;
  line-height: 72rpx;
}

.policy-row__dot {
  color: #97a39d;
}

.login-button {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  margin-top: 18rpx;
}

.login-panel__notice {
  display: block;
  margin-top: 22rpx;
  color: #74817b;
  font-size: 21rpx;
  line-height: 1.6;
}
</style>
