export const routes = {
  login: "/pages/auth/login",
  discover: "/pages/discover/index",
  matches: "/pages/matches/index",
  messages: "/pages/messages/index",
  me: "/pages/me/index",
  profileEdit: "/pages/profile/edit",
  projectList: "/pages/projects/list",
  projectEdit: "/pages/projects/edit",
  projectPreview: "/pages/projects/preview",
  projectResult: "/pages/projects/result",
} as const;

export type MainRoute = "discover" | "matches" | "messages" | "me";

export function openPage(url: string): void {
  uni.navigateTo({ url });
}

export function replacePage(url: string): void {
  uni.redirectTo({ url });
}

export function openMain(route: MainRoute): void {
  uni.reLaunch({ url: routes[route] });
}
