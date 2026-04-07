import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("api client", () => {
  beforeEach(() => {
    vi.resetModules();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("adds tenant header in the happy path", async () => {
    const { request, setTenantContext } = await import("./client");
    setTenantContext({ tenantCode: "vc" });

    fetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const payload = await request("/api/dashboard");

    expect(payload).toEqual({ ok: true });
    expect(fetch).toHaveBeenCalledWith(
      "/api/dashboard",
      expect.objectContaining({
        credentials: "include",
        headers: expect.objectContaining({
          "X-Tenant-Id": "vc",
          "Content-Type": "application/json",
        }),
      }),
    );
  });

  it("refreshes and retries once when the access token expired", async () => {
    const { request } = await import("./client");

    fetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Unauthorized" }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ refreshed: true }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ total_documents: 4 }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );

    const payload = await request("/api/dashboard");

    expect(payload).toEqual({ total_documents: 4 });
    expect(fetch).toHaveBeenNthCalledWith(
      2,
      "/api/auth/refresh",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
    expect(fetch).toHaveBeenCalledTimes(3);
  });

  it("surfaces backend detail when refresh cannot recover the request", async () => {
    const { request } = await import("./client");

    fetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Unauthorized" }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response("refresh failed", {
          status: 401,
          headers: { "content-type": "text/plain" },
        }),
      );

    await expect(request("/api/dashboard")).rejects.toThrow("refresh failed");
  });
});
