import { LayoutDashboard, Users, Sparkles, Activity } from 'lucide-react'

const nav = [
  { id: 'dashboard',       label: 'Dashboard',         icon: LayoutDashboard },
  { id: 'recommendations', label: 'Recommendations',   icon: Sparkles },
  { id: 'team',            label: 'Team Overview',      icon: Users },
]

export default function Sidebar({ current, onNavigate }) {
  return (
    <aside className="w-64 flex-shrink-0 flex flex-col bg-[#0f172a] border-r border-[#1e293b]">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-[#1e293b]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
            <Activity size={16} className="text-white" />
          </div>
          <div>
            <p className="text-white font-semibold text-sm leading-none">Sustayn</p>
            <p className="text-slate-500 text-xs mt-0.5">Retention-Aware Resourcing</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ id, label, icon: Icon }) => {
          const active = current === id
          return (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
                ${active
                  ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#1e293b]'
                }`}
            >
              <Icon size={16} className={active ? 'text-teal-400' : 'text-slate-500'} />
              {label}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-[#1e293b]">
        <p className="text-xs text-slate-600 leading-relaxed">
          IBM AI Builders Challenge<br />
          Wildcard: Intelligent Systems<br />
          for the Future of Work
        </p>
      </div>
    </aside>
  )
}
