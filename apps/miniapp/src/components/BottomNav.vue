<template>
  <view class="bottom-nav-wrap">
    <view class="bottom-nav">
      <button
        v-for="item in items"
        :key="item.key"
        class="bottom-nav__item"
        :class="{ 'bottom-nav__item--active': active === item.key }"
        :aria-label="item.label"
        @click="activate(item.key)"
      >
        <uni-icons
          :type="active === item.key ? item.activeIcon : item.icon"
          size="22"
          :color="active === item.key ? '#12664f' : '#74817b'"
        />
        <text class="bottom-nav__label">{{ item.label }}</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { openMain, type MainRoute } from "@/utils/navigation";

defineProps<{ active: MainRoute }>();

const items: Array<{
  key: MainRoute;
  label: string;
  icon: string;
  activeIcon: string;
}> = [
  { key: "discover", label: "发现", icon: "search", activeIcon: "search" },
  { key: "matches", label: "匹配", icon: "flag", activeIcon: "flag-filled" },
  { key: "messages", label: "消息", icon: "chat", activeIcon: "chat-filled" },
  { key: "me", label: "我的", icon: "person", activeIcon: "person-filled" },
];

function activate(route: MainRoute): void {
  openMain(route);
}
</script>

<style scoped>
.bottom-nav-wrap {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 20;
  padding: 0 20rpx env(safe-area-inset-bottom);
  border-top: 1rpx solid #dce4df;
  background: rgba(255, 255, 255, 0.97);
}

.bottom-nav {
  display: grid;
  width: 100%;
  max-width: 960rpx;
  height: 120rpx;
  margin: 0 auto;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.bottom-nav__item {
  display: flex;
  min-width: 0;
  min-height: 104rpx;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 6rpx;
  border-radius: 0;
  background: transparent;
  color: #74817b;
  line-height: 1;
}

.bottom-nav__item--active {
  color: #12664f;
}

.bottom-nav__label {
  font-size: 21rpx;
  font-weight: 600;
  line-height: 1.2;
}
</style>
