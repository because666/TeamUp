import { describe, expect, it } from "vitest";
import { AppServiceError } from "./runtime";
import { presentError } from "./presentation";

describe("service error presentation", () => {
  it.each([
    [401, "unauthenticated"],
    [403, "forbidden"],
    [409, "conflict"],
    [422, "validation_error"],
    [503, "network_error"],
  ] as const)("maps status %s to %s", (status, kind) => {
    const result = presentError(new AppServiceError("TEST_ERROR", "测试错误", status, "req_01"));

    expect(result.kind).toBe(kind);
    expect(result.requestId).toBe("req_01");
  });

  it("does not expose unknown exception details", () => {
    const result = presentError(new Error("internal database message"));

    expect(result.description).not.toContain("database");
    expect(result.kind).toBe("network_error");
  });

  it("keeps blocked-contact errors distinct from version conflicts", () => {
    const result = presentError(new AppServiceError("USER_BLOCKED", "服务端阻止交换", 409, "req_blocked"));

    expect(result.kind).toBe("forbidden");
    expect(result.title).toBe("当前无法联系项目组织者");
  });

  it("guides users to contact settings when their private card is missing", () => {
    const result = presentError(new AppServiceError(
      "CONTACT_CARD_REQUIRED",
      "contact value must stay private",
      409,
      "req_contact",
    ));

    expect(result.title).toBe("请先填写联系方式");
    expect(result.description).not.toContain("contact value");
  });
});
