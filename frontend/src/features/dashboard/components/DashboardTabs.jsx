import { NavLink } from "react-router-dom";
import { cn } from "@shared/lib";

const tabs = [
  { label: "Documentos", to: "/documentos" },
  { label: "Configuracion", to: "/configuracion" },
];

export function DashboardTabs() {
  return (
    <nav className="mt-5 flex flex-wrap gap-2">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) =>
            cn(
              "rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.2em] transition",
              isActive
                ? "border-emerald-900 bg-emerald-900 text-amber-100"
                : "border-emerald-200 bg-white text-emerald-800 hover:bg-emerald-50",
            )
          }
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
