import { z } from "zod";

export const settingsFormSchema = z.object({
  tenantName: z.string().trim().min(1, "Ingresa el nombre de la empresa."),
  tenantRut: z.string().trim().min(1, "Ingresa el RUT de la empresa."),
  siiEnvironment: z.enum(["certificacion", "produccion"]),
  siiRut: z.string().trim().min(1, "Ingresa el RUT para SII."),
  certificatePath: z.string().trim().min(1, "Ingresa la ruta del certificado."),
  certificatePassword: z.string().trim().optional(),
  pollIntervalMinutes: z.coerce.number().int().min(1, "El intervalo debe ser mayor a 0."),
  syncEnabled: z.boolean(),
});

export function buildSettingsFormValues(tenantForm, profileForm) {
  return {
    tenantName: tenantForm.name || "",
    tenantRut: tenantForm.rut || "",
    siiEnvironment: profileForm.sii_environment || "certificacion",
    siiRut: profileForm.sii_rut || "",
    certificatePath: profileForm.certificate_path || "",
    certificatePassword: profileForm.certificate_password || "",
    pollIntervalMinutes: Number(profileForm.poll_interval_minutes || 15),
    syncEnabled: Boolean(profileForm.sync_enabled),
  };
}

export function mapSettingsFormToPayload(values) {
  return {
    tenantForm: {
      name: values.tenantName,
      rut: values.tenantRut,
    },
    profileForm: {
      sii_environment: values.siiEnvironment,
      sii_rut: values.siiRut,
      sync_enabled: values.syncEnabled,
      poll_interval_minutes: values.pollIntervalMinutes,
      certificate_path: values.certificatePath,
      certificate_password: values.certificatePassword,
    },
  };
}
