import { AlertCircle, Info, ShieldCheck } from "lucide-react";
import { cn } from "@shared/lib";

const toneStyles = {
  success: {
    icon: ShieldCheck,
    container: "border-emerald-200 bg-emerald-50/85 text-emerald-900",
    iconClass: "text-emerald-700",
  },
  error: {
    icon: AlertCircle,
    container: "border-red-200 bg-red-50/90 text-red-900",
    iconClass: "text-red-700",
  },
  info: {
    icon: Info,
    container: "border-sky-200 bg-sky-50/85 text-sky-900",
    iconClass: "text-sky-700",
  },
};

export function FeedbackBanner({ feedback }) {
  const tone = toneStyles[feedback?.tone] || toneStyles.info;
  const Icon = tone.icon;

  return (
    <div
      className={cn(
        "mb-6 flex items-center gap-3 rounded-[1.2rem] border border-white/60 px-5 py-4 shadow-sm backdrop-blur-sm",
        tone.container,
      )}
    >
      <Icon size={18} className={cn("shrink-0", tone.iconClass)} />
      <p className="text-sm font-medium">{feedback?.message}</p>
    </div>
  );
}
