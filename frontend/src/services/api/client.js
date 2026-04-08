const JSON_HEADERS = {
  "Content-Type": "application/json",
};

let tenantContext = {
  tenantCode: "",
};
let refreshPromise = null;

export function setTenantContext(nextTenantContext = {}) {
  tenantContext = {
    tenantCode: nextTenantContext.tenantCode || "",
  };
}

export function getTenantContext() {
  return tenantContext;
}

async function executeRequest(path, options = {}) {
  return fetch(path, {
    credentials: "include",
    ...options,
    headers: {
      ...(tenantContext.tenantCode ? { "X-Tenant-Id": tenantContext.tenantCode } : {}),
      ...(options.body instanceof FormData ? {} : JSON_HEADERS),
      ...(options.headers || {}),
    },
  });
}

async function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    }).finally(() => {
      refreshPromise = null;
    });
  }

  const response = await refreshPromise;
  if (!response.ok) {
    const payload = await response.text();
    throw new Error(payload || "Session refresh failed");
  }
}

export async function request(path, options = {}) {
  const { skipAuthRefresh = false, ...fetchOptions } = options;

  let response = await executeRequest(path, fetchOptions);

  if (!skipAuthRefresh && (response.status === 401 || response.status === 403) && path !== "/api/auth/refresh") {
    await refreshSession();
    response = await executeRequest(path, fetchOptions);
  }

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof payload === "object" && payload?.detail ? payload.detail : "Request failed";
    throw new Error(message);
  }

  return payload;
}
