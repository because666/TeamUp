<template>
  <view class="page-shell page-shell--task">
    <view class="page-content">
      <BrandHeader caption="联系方式" back manual-back @back="requestLeave" />
      <FixtureBanner />

      <view v-if="loading" class="contact-loading">
        <view class="contact-loading__line" />
        <view class="contact-loading__field" />
        <view class="contact-loading__field" />
      </view>

      <view v-else-if="loadError" class="section">
        <StatusPanel
          :title="loadError.title"
          :description="loadError.description"
          tone="error"
          action-label="重试"
          @action="loadCard"
        />
      </view>

      <template v-else>
        <view class="privacy-note surface">
          <uni-icons type="locked" size="20" color="#12664f" />
          <view>
            <text class="privacy-note__title">默认不公开</text>
            <text class="privacy-note__copy">只有双方同意交换后，对方才能查看和复制。</text>
          </view>
        </view>

        <view class="section contact-form">
          <view class="field">
            <text class="field-label">微信号</text>
            <input
              v-model="wechat"
              class="text-input"
              maxlength="20"
              placeholder="6-20 位，以字母开头"
            />
            <text v-if="errors['CT-WECHAT']" class="field-error">{{ errors["CT-WECHAT"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">QQ</text>
            <input
              v-model="qq"
              class="text-input"
              type="number"
              maxlength="12"
              placeholder="5-12 位数字"
            />
            <text v-if="errors['CT-QQ']" class="field-error">{{ errors["CT-QQ"] }}</text>
          </view>

          <view class="field">
            <text class="field-label">邮箱</text>
            <input
              v-model="email"
              class="text-input"
              maxlength="254"
              placeholder="name@example.com"
            />
            <text v-if="errors['CT-EMAIL']" class="field-error">{{ errors["CT-EMAIL"] }}</text>
          </view>

          <text v-if="errors['CT-METHODS']" class="contact-form__error">{{ errors["CT-METHODS"] }}</text>

          <button class="primary-button contact-form__save" :disabled="saving" @click="saveCard">
            <uni-icons type="checkmarkempty" size="20" color="#ffffff" />
            <text>{{ saving ? "正在保存..." : "保存联系方式" }}</text>
          </button>

          <view v-if="feedback" class="contact-form__feedback" :class="{ 'contact-form__feedback--error': saveFailed }">
            <uni-icons
              :type="saveFailed ? 'info' : 'checkmarkempty'"
              size="17"
              :color="saveFailed ? '#a5372a' : '#12664f'"
            />
            <text>{{ feedback }}</text>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { onBackPress, onLoad } from "@dcloudio/uni-app";
import BrandHeader from "@/components/BrandHeader.vue";
import FixtureBanner from "@/components/FixtureBanner.vue";
import StatusPanel from "@/components/StatusPanel.vue";
import type { ContactCard, ContactMethod, FieldErrors } from "@/domain/models";
import { isValid, validateContactCard } from "@/domain/validation";
import { presentError, type ErrorPresentation } from "@/services/presentation";
import { repository } from "@/services/repository";

const loading = ref(true);
const saving = ref(false);
const loadError = ref<ErrorPresentation | null>(null);
const errors = ref<FieldErrors>({});
const wechat = ref("");
const qq = ref("");
const email = ref("");
const version = ref(0);
const confirmedSnapshot = ref("");
const feedback = ref("");
const saveFailed = ref(false);
let allowLeave = false;

const draft = computed<ContactCard>(() => {
  const methods: ContactMethod[] = [];
  if (wechat.value.trim()) methods.push({ type: "WECHAT", value: wechat.value.trim() });
  if (qq.value.trim()) methods.push({ type: "QQ", value: qq.value.trim() });
  if (email.value.trim()) methods.push({ type: "EMAIL", value: email.value.trim() });
  return { methods, version: version.value };
});
const dirty = computed(() => !loading.value && JSON.stringify(draft.value) !== confirmedSnapshot.value);

function applyCard(card: ContactCard | null): void {
  wechat.value = card?.methods.find((method) => method.type === "WECHAT")?.value || "";
  qq.value = card?.methods.find((method) => method.type === "QQ")?.value || "";
  email.value = card?.methods.find((method) => method.type === "EMAIL")?.value || "";
  version.value = card?.version || 0;
  confirmedSnapshot.value = JSON.stringify(draft.value);
}

async function loadCard(): Promise<void> {
  loading.value = true;
  loadError.value = null;
  try {
    applyCard((await repository.getContactCard()).data);
  } catch (error) {
    loadError.value = presentError(error);
  } finally {
    loading.value = false;
  }
}

async function saveCard(): Promise<void> {
  errors.value = validateContactCard(draft.value);
  feedback.value = "";
  saveFailed.value = false;
  if (!isValid(errors.value) || saving.value) return;
  saving.value = true;
  try {
    const saved = (await repository.saveContactCard(draft.value)).data;
    applyCard(saved);
    feedback.value = "联系方式已保存。";
  } catch (error) {
    const presentation = presentError(error);
    saveFailed.value = true;
    feedback.value = `${presentation.title}：${presentation.description}`;
  } finally {
    saving.value = false;
  }
}

function leave(): void {
  allowLeave = true;
  const pages = getCurrentPages();
  if (pages.length > 1) uni.navigateBack();
  else uni.reLaunch({ url: "/pages/me/index" });
}

function requestLeave(): void {
  if (!dirty.value) {
    leave();
    return;
  }
  uni.showModal({
    title: "放弃未保存修改？",
    content: "本页填写的联系方式尚未保存。",
    confirmText: "放弃",
    cancelText: "继续编辑",
    success: (result) => {
      if (result.confirm) leave();
    },
  });
}

onLoad(loadCard);
onBackPress(() => {
  if (allowLeave || !dirty.value) return false;
  requestLeave();
  return true;
});
</script>

<style scoped>
.contact-loading {
  padding: 48rpx 0;
}

.contact-loading__line,
.contact-loading__field {
  border-radius: 6rpx;
  background: #e3eae6;
}

.contact-loading__line {
  width: 44%;
  height: 26rpx;
}

.contact-loading__field {
  height: 92rpx;
  margin-top: 34rpx;
}

.privacy-note {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  margin-top: 28rpx;
  padding: 24rpx;
}

.privacy-note__title,
.privacy-note__copy {
  display: block;
}

.privacy-note__title {
  color: #23443a;
  font-size: 25rpx;
  font-weight: 800;
}

.privacy-note__copy {
  margin-top: 6rpx;
  color: #607069;
  font-size: 22rpx;
  line-height: 1.55;
}

.contact-form {
  border-top: 0;
}

.contact-form__error {
  display: block;
  margin-top: 20rpx;
  color: #b13b2d;
  font-size: 23rpx;
}

.contact-form__save {
  width: 100%;
  margin-top: 34rpx;
}

.contact-form__feedback {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  margin-top: 18rpx;
  color: #12664f;
  font-size: 22rpx;
  line-height: 1.5;
}

.contact-form__feedback--error {
  color: #a5372a;
}
</style>
