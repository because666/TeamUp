import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.resetModules();
});

function configureCloudbase(): void {
  vi.stubEnv("MODE", "cloudbase");
  vi.stubEnv("VITE_CLOUDBASE_ENV_ID", "teamup-dev-01");
  vi.stubEnv("VITE_CLOUDBASE_SERVICE", "teamup-api");
  vi.stubEnv("VITE_CLOUDBASE_API_PREFIX", "/api/v1");
}

describe("API transport", () => {
  it("maps an API request to the linked CloudBase container service", async () => {
    configureCloudbase();
    const init = vi.fn();
    const callContainer = vi.fn().mockResolvedValue({
      statusCode: 200,
      data: { data: { ok: true }, requestId: "req_cloudbase_01" },
    });
    vi.stubGlobal("wx", { cloud: { init, callContainer } });
    const { sendApiRequest } = await import("./transport");

    const response = await sendApiRequest({
      path: "/health/live",
      method: "GET",
      header: { "Content-Type": "application/json" },
    });

    expect(response.statusCode).toBe(200);
    expect(init).toHaveBeenCalledWith({ env: "teamup-dev-01" });
    expect(callContainer).toHaveBeenCalledWith({
      config: { env: "teamup-dev-01" },
      path: "/api/v1/health/live",
      method: "GET",
      data: undefined,
      header: {
        "Content-Type": "application/json",
        "X-WX-SERVICE": "teamup-api",
      },
    });
  });

  it("fails explicitly when CloudBase public configuration is missing", async () => {
    vi.stubEnv("MODE", "cloudbase");
    vi.stubEnv("VITE_CLOUDBASE_ENV_ID", "");
    vi.stubEnv("VITE_CLOUDBASE_SERVICE", "");
    const { sendApiRequest } = await import("./transport");

    await expect(sendApiRequest({
      path: "/health/live",
      method: "GET",
      header: {},
    })).rejects.toMatchObject({ code: "CLOUDBASE_NOT_CONFIGURED", status: 503 });
  });

  it("fails explicitly outside a WeChat runtime", async () => {
    configureCloudbase();
    const { sendApiRequest } = await import("./transport");

    await expect(sendApiRequest({
      path: "/health/live",
      method: "GET",
      header: {},
    })).rejects.toMatchObject({ code: "CLOUDBASE_UNAVAILABLE", status: 503 });
  });

  it("maps rejected container calls to a stable network error", async () => {
    configureCloudbase();
    vi.stubGlobal("wx", {
      cloud: {
        init: vi.fn(),
        callContainer: vi.fn().mockRejectedValue(new Error("provider detail")),
      },
    });
    const { sendApiRequest } = await import("./transport");

    await expect(sendApiRequest({
      path: "/health/live",
      method: "GET",
      header: {},
    })).rejects.toMatchObject({ code: "NETWORK_ERROR", status: 503 });
  });
});
