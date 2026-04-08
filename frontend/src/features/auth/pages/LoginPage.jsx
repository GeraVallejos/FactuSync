import { useState } from "react";
import { AlertCircle, Compass, Eye, EyeOff, Loader2, Lock, Mail, ShieldCheck } from "lucide-react";
import { useAuthContext } from "@app/providers";
import { Field, TextInput } from "@shared/ui";

const initialLoginForm = {
  username: "",
  password: "",
};

export function LoginPage() {
  const { busy, feedback, login } = useAuthContext();
  const [form, setForm] = useState(initialLoginForm);
  const [showPassword, setShowPassword] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    login(form);
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#f4f7f4] font-sans text-emerald-950">
      <div className="absolute left-0 top-0 h-2 w-full bg-linear-to-r from-emerald-800 via-emerald-600 to-amber-200" />
      <div className="absolute -left-[6%] -top-[10%] h-104 w-104 rounded-full bg-emerald-100/60 blur-3xl" />
      <div className="absolute -bottom-[12%] -right-[4%] h-112 w-md rounded-full bg-amber-50/80 blur-3xl" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-305 items-center justify-center px-6 py-12 lg:px-10">
        <div className="w-full max-w-140">
          <form
            className="rounded-[3rem] border border-white/65 bg-white/72 p-8 shadow-[0_30px_70px_rgba(2,44,34,0.12)] ring-1 ring-emerald-900/5 backdrop-blur-2xl sm:p-12"
            onSubmit={handleSubmit}
          >
            <div className="mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-[1.75rem] border border-white/80 bg-white/80 p-4 shadow-2xl shadow-emerald-900/10 ring-4 ring-white">
              <img src="/factysync.svg" alt="FactuSync" className="h-full w-full object-contain" />
            </div>
            <p className="text-center text-xs font-black uppercase tracking-[0.3em] text-emerald-700/70">
              Eldanor Software
            </p>
            <h1 className="mt-5 text-center font-serif text-5xl font-bold tracking-tight text-emerald-950 sm:text-6xl">
              Factu<span className="text-emerald-600">Sync</span>
            </h1>

            {feedback?.message ? (
              <div className="mt-8 flex items-center gap-3 rounded-2xl border border-red-100 bg-red-50/85 px-4 py-3 text-red-800">
                <AlertCircle size={18} className="shrink-0 text-red-600" />
                <p className="text-sm font-medium leading-tight">{feedback.message}</p>
              </div>
            ) : null}

            <div className="mt-8 space-y-6">
              <Field label="Usuario">
                <TextInput
                  icon={Mail}
                  value={form.username}
                  onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
                  placeholder="Usuario"
                  autoComplete="username"
                />
              </Field>

              <Field label="Contraseña">
                <div className="group relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-5 text-emerald-800/45 transition-colors group-focus-within:text-emerald-700">
                    <Lock size={20} />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={form.password}
                    onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                    placeholder="Contraseña"
                    autoComplete="current-password"
                    className="w-full rounded-[1.6rem] border border-emerald-100 bg-white/55 py-4 pl-13 pr-13 text-sm text-emerald-950 outline-none transition focus:border-emerald-600 focus:ring-8 focus:ring-emerald-50/70"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="absolute inset-y-0 right-0 flex items-center pr-5 text-emerald-800/40 transition hover:text-emerald-700"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </Field>
            </div>

            <button
              type="submit"
              disabled={busy}
              className="group mt-8 flex w-full items-center justify-center gap-3 rounded-[1.8rem] bg-emerald-900 px-6 py-5 text-xs font-black uppercase tracking-[0.3em] text-amber-100 shadow-2xl shadow-emerald-900/25 transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {busy ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin text-amber-200" />
                  <span>Conectando</span>
                </>
              ) : (
                <>
                  <span>Ingresar</span>
                  <Compass className="h-5 w-5 transition-transform group-hover:rotate-45" />
                </>
              )}
            </button>

            <div className="mt-10 flex items-center justify-center gap-3 border-t border-emerald-50 pt-7 text-center">
              <ShieldCheck size={18} className="text-emerald-800/40" />
              <span className="text-xs font-black uppercase tracking-[0.35em] text-emerald-800/35">Acceso seguro</span>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
