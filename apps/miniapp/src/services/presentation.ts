import { AppServiceError } from "./runtime";

export type ErrorViewKind =
  | "network_error"
  | "unauthenticated"
  | "forbidden"
  | "conflict"
  | "validation_error";

export interface ErrorPresentation {
  kind: ErrorViewKind;
  title: string;
  description: string;
  requestId: string;
}

export function presentError(error: unknown): ErrorPresentation {
  if (!(error instanceof AppServiceError)) {
    return {
      kind: "network_error",
      title: "暂时无法连接服务",
      description: "请检查网络后重试，当前输入仍保留在本机。",
      requestId: "local_request",
    };
  }

  if (error.status === 401) {
    return {
      kind: "unauthenticated",
      title: "登录状态已失效",
      description: "请重新登录。安全的本地草稿会继续保留。",
      requestId: error.requestId,
    };
  }
  if (error.status === 403) {
    return {
      kind: "forbidden",
      title: "当前账号无法执行此操作",
      description: "请返回安全页面，不会显示更多资源信息。",
      requestId: error.requestId,
    };
  }
  if (error.status === 409) {
    return {
      kind: "conflict",
      title: "内容已在其他位置更新",
      description: "请重新加载最新版本；系统不会自动覆盖你的修改。",
      requestId: error.requestId,
    };
  }
  if (error.status === 422) {
    return {
      kind: "validation_error",
      title: "还有内容需要确认",
      description: error.message,
      requestId: error.requestId,
    };
  }

  return {
    kind: "network_error",
    title: error.code === "BACKEND_NOT_CONFIGURED" ? "真实服务尚未接入" : "请求未完成",
    description: error.message,
    requestId: error.requestId,
  };
}
