import { describe, expect, it } from "vitest";
import { projectDetailRoute } from "./navigation";

describe("project detail navigation", () => {
  it("encodes the selected project id in the page route", () => {
    expect(projectDetailRoute("project/id 01")).toBe("/pages/projects/detail?id=project%2Fid%2001");
  });
});
