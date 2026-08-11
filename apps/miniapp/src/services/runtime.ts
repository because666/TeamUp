export type RuntimeMode = "fixture" | "api";

export const runtimeMode: RuntimeMode = import.meta.env.MODE === "fixture" ? "fixture" : "api";

export const isFixtureMode = (): boolean => runtimeMode === "fixture";

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
