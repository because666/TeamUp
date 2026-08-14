export type RuntimeMode = "fixture" | "api";

export const runtimeMode: RuntimeMode = import.meta.env.MODE === "fixture" ? "fixture" : "api";

export const isFixtureMode = (): boolean => runtimeMode === "fixture";
export const isApiMode = (): boolean => runtimeMode === "api";

export function apiBaseUrl(): string {
  const value = String(import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");
  if (!value) {
    throw new AppServiceError(
      "BACKEND_NOT_CONFIGURED",
      "真实服务尚未配置 API 地址，请先设置 VITE_API_BASE_URL。",
      503,
    );
  }
  const isHttps = value.startsWith("https://");
  const isLocalHttp = /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?(\/|$)/.test(value);
  if (!isHttps && !isLocalHttp) {
    throw new AppServiceError(
      "BACKEND_URL_INSECURE",
      "真实服务必须使用 HTTPS；本地开发只允许 localhost 或 127.0.0.1。",
      503,
    );
  }
  return value;
}

export class AppServiceError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId: string;

  constructor(code: string, message: string, status = 503, requestId = "local_request") {
    super(message);
    this.name = "AppServiceError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

export function requireFixtureMode(): void {
  if (!isFixtureMode()) {
    throw new AppServiceError(
      "BACKEND_NOT_CONFIGURED",
      "真实接口尚未完成契约配置，请切换到合约模拟模式。",
    );
  }
}
