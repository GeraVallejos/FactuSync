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
      { label: "Ambiente", value: profileForm.sii_environment === "produccion" ? "Produccion" : "Certificacion" },
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
      subtitle="Primero ves el resumen operativo; el detalle avanzado aparece solo cuando lo necesitas."
      actions={
        <>
          <button
            className="rounded-full border border-emerald-200 bg-white px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-emerald-800 transition hover:bg-emerald-50 disabled:opacity-60"
            onClick={handleSubmit(submitTest)}
            disabled={busy}
            type="button"
          >
            Probar SII
          </button>
          <button
            className="rounded-full bg-emerald-900 px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-amber-100 transition hover:bg-emerald-800 disabled:opacity-60"
            onClick={handleSubmit(submitSave)}
            disabled={busy}
            type="button"
          >
            Guardar
          </button>
          <button
            className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white px-4 py-2 text-xs font-bold uppercase tracking-[0.2em] text-emerald-800 transition hover:bg-emerald-50"
            onClick={() => setExpanded((current) => !current)}
            type="button"
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {expanded ? "Ocultar detalle" : "Editar detalle"}
          </button>
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-4">
        {summaryItems.map((item) => (
          <div key={item.label} className="rounded-[1.5rem] border border-emerald-100 bg-white/70 p-4">
            <p className="text-[11px] font-black uppercase tracking-[0.22em] text-emerald-700/55">{item.label}</p>
            <p className="mt-3 text-sm font-semibold text-emerald-950">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-3 rounded-[1.5rem] border border-emerald-100 bg-emerald-50/70 px-4 py-3 text-sm text-emerald-900/70">
        <ShieldCheck size={16} className="text-emerald-700" />
        <span>
          Usa "Probar SII" para validar credenciales sin salir de esta pantalla.
          {isDirty ? " Hay cambios sin guardar." : ""}
        </span>
      </div>

      {expanded ? (
        <form className="mt-6 grid gap-5 lg:grid-cols-2" onSubmit={handleSubmit(submitSave)}>
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
            <label className="flex w-full items-center gap-3 rounded-[1.6rem] border border-emerald-100 bg-white/55 px-5 py-4 text-sm font-medium text-emerald-950">
              <input
                type="checkbox"
                {...register("syncEnabled")}
                className="h-4 w-4 rounded border-emerald-300 text-emerald-700"
              />
              Habilitar sincronización con SII
            </label>
          </div>
        </form>
      ) : null}
    </SectionCard>
  );
}

function FieldError({ message }) {
  return <span className="ml-1 text-xs font-medium text-red-700">{message}</span>;
}
