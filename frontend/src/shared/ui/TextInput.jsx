import { forwardRef } from "react";

export const TextInput = forwardRef(function TextInput({ icon: Icon, className = "", ...props }, ref) {
  return (
    <div className="group relative">
      {Icon ? (
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4 text-slate-400 transition-colors group-focus-within:text-emerald-600">
          <Icon size={18} />
        </div>
      ) : null}
      <input
        ref={ref}
        className={`w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-500/10 ${Icon ? "pl-11" : ""} ${className}`}
        {...props}
      />
    </div>
  );
});
