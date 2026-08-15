<script setup lang="ts">
import { onLaunch } from "@dcloudio/uni-app";

onLaunch(() => undefined);
</script>

<style>
page {
  min-height: 100%;
  background: #f6f8f7;
  color: #17231e;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 28rpx;
}

view,
text,
button,
input,
textarea,
scroll-view {
  box-sizing: border-box;
  letter-spacing: 0;
}

button {
  margin: 0;
  transition: background-color 160ms ease, border-color 160ms ease, color 160ms ease,
    transform 160ms ease;
}

button::after {
  border: 0;
}

.page-shell {
  min-height: 100vh;
  padding: 0 28rpx calc(176rpx + env(safe-area-inset-bottom));
}

.page-shell--task {
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
}

.page-content {
  width: 100%;
  max-width: 900rpx;
  margin: 0 auto;
}

.section {
  padding: 38rpx 0;
  border-top: 1rpx solid #dfe6e2;
}

.section:first-child {
  border-top: 0;
}

.section-title {
  display: block;
  margin: 0;
  color: #17231e;
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.4;
}

.section-copy {
  display: block;
  margin-top: 8rpx;
  color: #69776f;
  font-size: 24rpx;
  line-height: 1.55;
}

.field {
  margin-top: 30rpx;
}

.field-label {
  display: block;
  margin-bottom: 14rpx;
  color: #2b3933;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1.4;
}

.field-hint,
.field-error {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  line-height: 1.45;
}

.field-hint {
  color: #74817b;
}

.field-error {
  color: #b13b2d;
}

.text-input,
.text-area {
  width: 100%;
  border: 1rpx solid #c7d3cd;
  border-radius: 8rpx;
  background: #ffffff;
  color: #17231e;
  font-size: 28rpx;
}

.text-input {
  height: 92rpx;
  padding: 0 24rpx;
}

.text-area {
  min-height: 200rpx;
  padding: 22rpx 24rpx;
  line-height: 1.55;
}

.text-input:focus,
.text-area:focus {
  border-color: #12664f;
  box-shadow: 0 0 0 4rpx rgba(22, 129, 94, 0.12);
}

.primary-button,
.secondary-button,
.text-button,
.danger-button {
  display: inline-flex;
  min-height: 92rpx;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  border-radius: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.2;
}

.primary-button {
  background: #12664f;
  color: #ffffff;
}

.primary-button:active {
  background: #0e5743;
  transform: translateY(1rpx);
}

.primary-button[disabled] {
  background: #a9b9b2;
  color: #eef2f0;
}

.secondary-button {
  border: 1rpx solid #b9c8c1;
  background: #ffffff;
  color: #244038;
}

.secondary-button:active,
.text-button:active {
  background: #eef4f1;
}

.text-button {
  min-height: 76rpx;
  background: transparent;
  color: #12664f;
}

.danger-button {
  border: 1rpx solid #e3b7b0;
  background: #fff8f6;
  color: #a5372a;
}

.button-row {
  display: flex;
  gap: 18rpx;
  margin-top: 32rpx;
}

.button-row button {
  flex: 1;
}

.surface {
  border: 1rpx solid #d8e2dd;
  border-radius: 8rpx;
  background: #ffffff;
}

.divider {
  height: 1rpx;
  background: #dfe6e2;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
