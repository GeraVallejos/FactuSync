import { describe, expect, it } from "vitest";
import { mapSession } from "./sessionMappers";

describe("mapSession", () => {
  it("maps the primary membership in the happy path", () => {
    const session = mapSession({
      memberships: [
        {
          tenant_code: "vc",
          operation_mode: "standalone",
          tenant_name: "ValCri",
        },
      ],
    });

    expect(session.primaryMembership).toEqual({
      tenantCode: "vc",
      operationMode: "standalone",
      tenantName: "ValCri",
    });
    expect(session.memberships).toHaveLength(1);
  });

  it("returns safe defaults when memberships are missing", () => {
    const session = mapSession({});

    expect(session.primaryMembership).toEqual({
      tenantCode: "",
      operationMode: "standalone",
      tenantName: "Sin empresa",
    });
    expect(session.memberships).toEqual([]);
  });
});
