import { useEffect, useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";
import { buildSettingsFormValues, mapSettingsFormToPayload, settingsFormSchema } from "@features/dashboard/forms/settingsFormSchema";
import { Field, SectionCard, SelectInput, TextInput } from "@shared/ui";

export function SettingsPanel({ tenantForm, profileForm, onSave, onTestAuth, busy }) {
  const [expanded, setExpanded] = useState(false);

  const form = useForm({
    resolver: zodResolver(settingsFormSchema),
    defaultValues: buildSettingsFormValues(tenantForm, profileForm),
  });

  const { formState, handleSubmit, register, reset } = form;
  const { errors, isDirty } = formState;

  useEffect(() => {
    reset(buildSettingsFormValues(tenantForm, profileForm));
  }, [profileForm, reset, tenantForm]);

  const summaryItems = useMemo(
    () => [
      { label: "Empresa", value: tenantForm.name || "Sin nombre" },
      { label: "RUT", value: tenantForm.rut || "Sin RUT" },
      { label: "Ambiente", value: profileForm.sii_environment === "produccion" ? "Producción" : "Certificación" },
      { label: "Sync", value: profileForm.sync_enabled ? "Habilitado" : "Manual" },
    ],
    [profileForm.sii_environment, profileForm.sync_enabled, tenantForm.name, tenantForm.rut],
  );

  function submitSave(values) {
    onSave(mapSettingsFormToPayload(values));
  }

  function submitTest(values) {
    onTestAuth(mapSettingsFormToPayload(values));
  }

  return (
    <SectionCard
      title="Configuración tributaria"
      subtitle="Resumen operativo y acceso rápido a tus credenciales SII y parámetros de sincronización."
      actions={
        <>
          <button
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
            onClick={handleSubmit(submitTest)}
            disabled={busy}
            type="button"
          >
            Probar SII
          </button>
          <button
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:opacity-60"
            onClick={handleSubmit(submitSave)}
            disabled={busy}
            type="button"
          >
            Guardar
          </button>
        </>
      }
    >
      <div className="grid gap-4 xl:grid-cols-[0.95fr_1.45fr]">
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-2">
            {summaryItems.map((item) => (
              <div key={item.label} className="rounded-[1rem] border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400">{item.label}</p>
                <p className="mt-3 text-sm font-semibold text-slate-900">{item.value}</p>
              </div>
            ))}
          </div>

          <div className="rounded-[1rem] border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-900/80">
            <div className="flex items-start gap-3">
              <ShieldCheck size={16} className="mt-0.5 shrink-0 text-emerald-700" />
              <p className="leading-6">
                Usa "Probar SII" para validar credenciales sin salir de esta pantalla.
                {isDirty ? " Hay cambios sin guardar." : ""}
              </p>
            </div>
          </div>

          <button
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            onClick={() => setExpanded((current) => !current)}
            type="button"
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {expanded ? "Ocultar detalle" : "Editar detalle"}
          </button>
        </div>

        <div className="rounded-[1.25rem] border border-slate-200 bg-white/70 p-5 shadow-sm">
          <div className="mb-5">
            <h3 className="text-base font-bold text-slate-900">Datos tributarios</h3>
            <p className="mt-1 text-sm text-slate-500">
              Mantén alineados los datos de empresa, ambiente y certificados con tu operación actual.
            </p>
          </div>

          {expanded ? (
            <form className="grid gap-5 lg:grid-cols-2" onSubmit={handleSubmit(submitSave)}>
              <Field label="Nombre de la empresa">
                <TextInput {...register("tenantName")} />
                {errors.tenantName ? <FieldError message={errors.tenantName.message} /> : null}
              </Field>

              <Field label="RUT de la empresa">
                <TextInput {...register("tenantRut")} />
                {errors.tenantRut ? <FieldError message={errors.tenantRut.message} /> : null}
              </Field>

              <Field label="Ambiente SII">
                <SelectInput {...register("siiEnvironment")}>
                  <option value="certificacion">Certificación</option>
                  <option value="produccion">Producción</option>
                </SelectInput>
                {errors.siiEnvironment ? <FieldError message={errors.siiEnvironment.message} /> : null}
              </Field>

              <Field label="RUT SII">
                <TextInput {...register("siiRut")} />
                {errors.siiRut ? <FieldError message={errors.siiRut.message} /> : null}
              </Field>

              <Field label="Ruta del certificado" hint="Ruta local al archivo .pfx o .p12 del certificado tributario.">
                <TextInput {...register("certificatePath")} placeholder="C:\\certificados\\empresa.pfx" />
                {errors.certificatePath ? <FieldError message={errors.certificatePath.message} /> : null}
              </Field>

              <Field label="Clave del certificado">
                <TextInput type="password" {...register("certificatePassword")} placeholder="Clave del .pfx/.p12" />
                {errors.certificatePassword ? <FieldError message={errors.certificatePassword.message} /> : null}
              </Field>

              <Field label="Intervalo de sincronización (min)">
                <TextInput type="number" min="1" {...register("pollIntervalMinutes", { valueAsNumber: true })} />
                {errors.pollIntervalMinutes ? <FieldError message={errors.pollIntervalMinutes.message} /> : null}
              </Field>

              <div className="flex items-end">
                <label className="flex w-full items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900">
                  <input
                    type="checkbox"
                    {...register("syncEnabled")}
                    className="h-4 w-4 rounded border-emerald-300 text-emerald-700"
                  />
                  Habilitar sincronización con SII
                </label>
              </div>
            </form>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-500">
              Activa "Editar detalle" para modificar credenciales, certificados y parámetros de sincronización.
            </div>
          )}
        </div>
      </div>
    </SectionCard>
  );
}

function FieldError({ message }) {
  return <span className="ml-1 text-xs font-medium text-red-700">{message}</span>;
}
