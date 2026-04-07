import { forwardRef } from "react";

export const SelectInput = forwardRef(function SelectInput(props, ref) {
  return (
    <select
      ref={ref}
      className="w-full rounded-[1.6rem] border border-emerald-100 bg-white/55 px-5 py-4 text-sm text-emerald-950 outline-none transition focus:border-emerald-600 focus:ring-8 focus:ring-emerald-50/70"
      {...props}
    />
  );
});
