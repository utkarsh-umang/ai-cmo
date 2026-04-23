const COLORS = {
  green: "text-emerald-500",
  blue: "text-brand-500",
  purple: "text-brand-500",
  gray: "text-slate-300",
  red: "text-rose-500",
};

export function StatusBadge({
  label,
  value,
  color = "gray",
}: {
  label: string;
  value: string;
  color?: keyof typeof COLORS;
}) {
  return (
    <div className="flex flex-col items-start">
      <p className="text-[10px] font-medium uppercase tracking-widest text-slate-400 mb-0.5">{label}</p>
      <p className={`text-2xl font-light tracking-tight ${COLORS[color]}`}>{value}</p>
    </div>
  );
}
