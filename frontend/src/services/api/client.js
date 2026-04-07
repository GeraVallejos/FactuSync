const JSON_HEADERS = {
  "Content-Type": "application/json",
};

let tenantContext = {
  tenantCode: "",
};

export function setTenantContext(nextTenantContext = {}) {
  tenantContext = {
    tenantCode: nextTenantContext.tenantCode || "",
  };
}

export async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    ...options,
    headers: {
      ...(tenantContext.tenantCode ? { "X-Tenant-Id": tenantContext.tenantCode } : {}),
      ...(options.body instanceof FormData ? {} : JSON_HEADERS),
      ...(options.headers || {}),
    },
  });

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
