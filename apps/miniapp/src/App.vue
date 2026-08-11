<script setup lang="ts">
import { onLaunch } from "@dcloudio/uni-app";

onLaunch(() => undefined);
</script>

<style>
page {
  min-height: 100%;
  background: #f4f7f5;
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
}

button::after {
  border: 0;
}

.page-shell {
  min-height: 100vh;
  padding: 0 32rpx calc(176rpx + env(safe-area-inset-bottom));
}

.page-shell--task {
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
}

.page-content {
  width: 100%;
  max-width: 960rpx;
  margin: 0 auto;
}

.section {
  padding: 34rpx 0;
  border-top: 1rpx solid #dce4df;
}

.section:first-child {
  border-top: 0;
}

.section-title {
  display: block;
  margin: 0;
  color: #17231e;
  font-size: 34rpx;
  font-weight: 700;
  line-height: 1.35;
}

.section-copy {
  display: block;
  margin-top: 10rpx;
  color: #607069;
  font-size: 25rpx;
  line-height: 1.6;
}

.field {
  margin-top: 28rpx;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: #2b3933;
  font-size: 25rpx;
  font-weight: 600;
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
  border: 1rpx solid #cfd9d3;
  border-radius: 8rpx;
  background: #ffffff;
  color: #17231e;
  font-size: 28rpx;
}

.text-input {
  height: 88rpx;
  padding: 0 24rpx;
}

.text-area {
  min-height: 192rpx;
  padding: 20rpx 24rpx;
  line-height: 1.55;
}

.text-input:focus,
.text-area:focus {
  border-color: #16815e;
  box-shadow: 0 0 0 4rpx rgba(22, 129, 94, 0.12);
}

.primary-button,
.secondary-button,
.text-button,
.danger-button {
  min-height: 88rpx;
  border-radius: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 88rpx;
}

.primary-button {
  background: #12664f;
  color: #ffffff;
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

.text-button {
  min-height: 72rpx;
  background: transparent;
  color: #12664f;
  line-height: 72rpx;
}

.danger-button {
  border: 1rpx solid #e3b7b0;
  background: #fff8f6;
  color: #a5372a;
}

.button-row {
  display: flex;
  gap: 16rpx;
  margin-top: 34rpx;
}

.button-row button {
  flex: 1;
}

.surface {
  border: 1rpx solid #dbe3df;
  border-radius: 8rpx;
  background: #ffffff;
}

.divider {
  height: 1rpx;
  background: #dce4df;
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
