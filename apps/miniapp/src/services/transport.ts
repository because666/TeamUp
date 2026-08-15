import {
  apiBaseUrl,
  apiTransportMode,
  AppServiceError,
  cloudbaseRuntimeConfig,
} from "./runtime";

export type ApiMethod = "GET" | "POST" | "PUT";

export interface TransportRequest {
  path: string;
  method: ApiMethod;
  data?: unknown;
  header: Record<string, string>;
}

export interface TransportResponse {
  statusCode: number;
  data: unknown;
}

interface CloudContainerResponse {
  statusCode: number;
  data: unknown;
}

interface WechatCloudApi {
  init(options: { env: string }): void;
  callContainer(options: {
    config: { env: string };
    path: string;
    method: ApiMethod;
    data?: unknown;
    header: Record<string, string>;
  }): Promise<CloudContainerResponse>;
}

let initializedCloudbaseEnv = "";

function cloudApi(): WechatCloudApi {
  const runtime = globalThis as typeof globalThis & {
    wx?: { cloud?: WechatCloudApi };
  };
  const cloud = runtime.wx?.cloud;
  if (!cloud || typeof cloud.init !== "function" || typeof cloud.callContainer !== "function") {
    throw new AppServiceError(
      "CLOUDBASE_UNAVAILABLE",
      "当前环境无法连接微信云托管，请使用微信小程序环境。",
      503,
    );
  }
  return cloud;
}

function httpRequest(request: TransportRequest): Promise<TransportResponse> {
  return new Promise((resolve, reject) => {
    let baseUrl: string;
    try {
      baseUrl = apiBaseUrl();
    } catch (error) {
      reject(error);
      return;
    }

    uni.request({
      url: `${baseUrl}${request.path}`,
      method: request.method,
      data: request.data as UniApp.RequestOptions["data"],
      header: request.header,
      timeout: 10000,
      success: (response) => resolve({ statusCode: response.statusCode, data: response.data }),
      fail: () => reject(new AppServiceError(
        "NETWORK_ERROR",
        "暂时无法连接服务，请检查网络后重试。",
        503,
      )),
    });
  });
}

async function cloudbaseRequest(request: TransportRequest): Promise<TransportResponse> {
  const config = cloudbaseRuntimeConfig();
  const cloud = cloudApi();
  try {
    if (initializedCloudbaseEnv !== config.envId) {
      cloud.init({ env: config.envId });
      initializedCloudbaseEnv = config.envId;
    }
    const response = await cloud.callContainer({
      config: { env: config.envId },
      path: `${config.apiPrefix}${request.path}`,
      method: request.method,
      data: request.data,
      header: {
        ...request.header,
        "X-WX-SERVICE": config.serviceName,
      },
    });
    return { statusCode: response.statusCode, data: response.data };
  } catch (error) {
    if (error instanceof AppServiceError) throw error;
    throw new AppServiceError(
      "NETWORK_ERROR",
      "暂时无法连接微信云托管服务，请稍后重试。",
      503,
    );
  }
}

export function sendApiRequest(request: TransportRequest): Promise<TransportResponse> {
  return apiTransportMode() === "cloudbase"
    ? cloudbaseRequest(request)
    : httpRequest(request);
}
