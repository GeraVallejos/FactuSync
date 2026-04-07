export function formatCurrency(value, locale = "es-CL", currency = "CLP") {
  return Number(value || 0).toLocaleString(locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  });
}

export function formatFallback(value, fallback) {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return value;
}

export function joinMessages(messages, fallback = "") {
  if (!Array.isArray(messages) || messages.length === 0) {
    return fallback;
  }

  return messages.join("; ");
}
