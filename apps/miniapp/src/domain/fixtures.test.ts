import { describe, expect, it } from "vitest";
import { discoveryProjectDetails, discoveryProjects, fixtureEnvelope } from "./fixtures";

describe("contract fixtures", () => {
  it("always declares fixture and proposed gap provenance", () => {
    const envelope = fixtureEnvelope({ ok: true }, ["GAP-AUTH-01"]);

    expect(envelope._fixture).toBe(true);
    expect(envelope.contractStatus).toBe("PROPOSED_GAP");
    expect(envelope.gapIds).toEqual(["GAP-AUTH-01"]);
    expect(envelope.requestId).toMatch(/^fixture_request_/);
  });

  it("uses unmistakable fixture ids for discovery content", () => {
    expect(discoveryProjects.length).toBeGreaterThan(0);
    expect(discoveryProjects.every((project) => project.id.startsWith("fixture_"))).toBe(true);
    expect(discoveryProjectDetails.map((project) => project.id)).toEqual(
      discoveryProjects.map((project) => project.id),
    );
  });
});
