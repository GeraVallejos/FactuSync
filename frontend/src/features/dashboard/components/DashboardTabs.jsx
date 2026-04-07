import { FileText, Settings } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@shared/lib";

const tabs = [
  { label: "Documentos", to: "/documentos", icon: FileText },
  { label: "Configuración", to: "/configuracion", icon: Settings },
];

export function DashboardTabs() {
  return (
    <nav className="flex flex-wrap items-center gap-1 rounded-xl border border-slate-200 bg-slate-100 p-1">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) =>
            cn(
              "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition",
              isActive
                ? "bg-white text-emerald-700 shadow-sm"
                : "text-slate-500 hover:bg-white hover:text-slate-700",
            )
          }
        >
          <tab.icon size={16} />
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
