import { forwardRef } from "react";

export const TextInput = forwardRef(function TextInput({ icon: Icon, className = "", ...props }, ref) {
  return (
    <div className="group relative">
      {Icon ? (
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-5 text-emerald-800/45 transition-colors group-focus-within:text-emerald-700">
          <Icon size={20} />
        </div>
      ) : null}
      <input
        ref={ref}
        className={`w-full rounded-[1.6rem] border border-emerald-100 bg-white/55 px-5 py-4 text-sm text-emerald-950 outline-none transition focus:border-emerald-600 focus:ring-8 focus:ring-emerald-50/70 ${Icon ? "pl-13" : ""} ${className}`}
        {...props}
      />
    </div>
  );
});
