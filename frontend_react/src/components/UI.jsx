export function Card({ children, className = '' }) {
  return (
    <div className={`bg-[#0f172a] border border-[#1e293b] rounded-xl p-5 ${className}`}>
      {children}
    </div>
  )
}

export function StatCard({ label, value, sub, accent = false, danger = false }) {
  return (
    <div className={`bg-[#0f172a] border rounded-xl p-5
      ${danger ? 'border-red-500/30' : accent ? 'border-teal-500/30' : 'border-[#1e293b]'}`}>
      <p className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-3xl font-bold
        ${danger ? 'text-red-400' : accent ? 'text-teal-400' : 'text-white'}`}>
        {value}
      </p>
      {sub && <p className="text-slate-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}

export function Badge({ variant = 'default', children }) {
  const styles = {
    red:     'bg-red-500/10 text-red-400 border-red-500/20',
    amber:   'bg-amber-500/10 text-amber-400 border-amber-500/20',
    green:   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    teal:    'bg-teal-500/10 text-teal-400 border-teal-500/20',
    default: 'bg-slate-700/50 text-slate-300 border-slate-600/50',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${styles[variant]}`}>
      {children}
    </span>
  )
}

export function ScoreBar({ value, max = 1, color = 'teal' }) {
  const pct = Math.min(100, (value / max) * 100)
  const colors = {
    teal:    'bg-teal-500',
    red:     'bg-red-400',
    amber:   'bg-amber-400',
    emerald: 'bg-emerald-500',
  }
  return (
    <div className="w-full bg-[#1e293b] rounded-full h-1.5">
      <div
        className={`h-1.5 rounded-full transition-all ${colors[color] || 'bg-teal-500'}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-8 h-8 border-2 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
    </div>
  )
}

export function ErrorMsg({ message }) {
  return (
    <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm">
      {message}
    </div>
  )
}
