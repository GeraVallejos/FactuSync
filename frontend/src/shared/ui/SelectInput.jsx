import { forwardRef } from "react";

export const SelectInput = forwardRef(function SelectInput(props, ref) {
  return (
    <select
      ref={ref}
      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-500/10"
      {...props}
    />
  );
});
