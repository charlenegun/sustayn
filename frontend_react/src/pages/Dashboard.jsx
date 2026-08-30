import { useEffect, useState } from 'react'
import { AlertTriangle, TrendingUp, Users, Zap, ArrowRight } from 'lucide-react'
import { fetchTeamOverview } from '../api'
import { StatCard, Card, Spinner, ErrorMsg } from '../components/UI'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'

export default function Dashboard({ onNavigate }) {
  const [team, setTeam] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchTeamOverview()
      .then(setTeam)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8"><Spinner /></div>
  if (error) return <div className="p-8"><ErrorMsg message={`Cannot reach backend: ${error}`} /></div>

  const highRisk   = team.filter(e => e.attrition_risk_score >= 0.6).length
  const overloaded = team.filter(e => e.tasks_assigned >= 4).length
  const danger     = team.filter(e => e.attrition_risk_score >= 0.6 && e.tasks_assigned >= 4).length
  const total      = team.length

  const riskDist = [
    { name: 'Low (<40%)',     value: team.filter(e => e.attrition_risk_score < 0.4).length,  fill: '#10b981' },
    { name: 'Medium (40-60%)', value: team.filter(e => e.attrition_risk_score >= 0.4 && e.attrition_risk_score < 0.6).length, fill: '#fbbf24' },
    { name: 'High (≥60%)',    value: highRisk, fill: '#f87171' },
  ]

  // Top 5 highest-risk overloaded employees
  const topDanger = team
    .filter(e => e.attrition_risk_score >= 0.6 && e.tasks_assigned >= 4)
    .sort((a, b) => b.attrition_risk_score - a.attrition_risk_score)
    .slice(0, 5)

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Real-time view of team risk and workload across {total} employees.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Employees" value={total} sub="from IBM HR dataset" />
        <StatCard label="Elevated Risk" value={highRisk} sub="attrition risk ≥ 60%" accent />
        <StatCard label="Near Capacity" value={overloaded} sub="tasks assigned ≥ 4/5" />
        <StatCard label="Danger Zone" value={danger} sub="high risk + high load" danger />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Risk distribution chart */}
        <Card>
          <h2 className="text-white font-semibold mb-1">Risk Distribution</h2>
          <p className="text-slate-500 text-xs mb-4">Employees by attrition risk band</p>
          <div className="flex items-center gap-6">
            <ResponsiveContainer width={140} height={140}>
              <RadialBarChart
                cx="50%" cy="50%"
                innerRadius={25} outerRadius={65}
                data={riskDist}
                startAngle={90} endAngle={-270}
              >
                <RadialBar dataKey="value" cornerRadius={4} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#f1f5f9' }}
                />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="space-y-2.5">
              {riskDist.map(d => (
                <div key={d.name} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: d.fill }} />
                  <span className="text-slate-400 text-xs">{d.name}</span>
                  <span className="text-white text-xs font-semibold ml-auto pl-4">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Scoring formula explainer */}
        <Card>
          <h2 className="text-white font-semibold mb-1">How Scoring Works</h2>
          <p className="text-slate-500 text-xs mb-4">The matching engine formula</p>
          <div className="bg-[#0a0f1e] rounded-lg p-4 font-mono text-xs leading-6">
            <p className="text-teal-400">score =</p>
            <p className="text-slate-300 pl-4">skill_fit_score</p>
            <p className="text-slate-300 pl-4">− risk_penalty <span className="text-slate-500">(only if risk {'>'} 60% AND tasks ≥ 4)</span></p>
            <p className="text-slate-300 pl-4">+ availability × 0.3</p>
          </div>
          <div className="mt-4 space-y-2 text-xs text-slate-400">
            <p>• <span className="text-white">Skill fit</span> — % of required skills matched</p>
            <p>• <span className="text-white">Risk penalty</span> — only fires on compound condition</p>
            <p>• <span className="text-white">Availability</span> — remaining headroom (ceiling: 5 tasks)</p>
          </div>
        </Card>
      </div>

      {/* Danger zone table */}
      {topDanger.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-400" />
              <h2 className="text-white font-semibold">Danger Zone</h2>
              <span className="text-xs text-slate-500 ml-1">— high risk + high workload, do not assign new tasks</span>
            </div>
            <button
              onClick={() => onNavigate('team')}
              className="flex items-center gap-1 text-teal-400 text-xs hover:text-teal-300 transition-colors"
            >
              View all <ArrowRight size={12} />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#1e293b]">
                  {['Employee #', 'Role', 'Department', 'Attrition Risk', 'Tasks'].map(h => (
                    <th key={h} className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider pb-2 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e293b]">
                {topDanger.map(e => (
                  <tr key={e.EmployeeNumber} className="hover:bg-[#1e293b]/50 transition-colors">
                    <td className="py-2.5 pr-4 text-slate-300 font-mono text-xs">#{e.EmployeeNumber}</td>
                    <td className="py-2.5 pr-4 text-white text-xs">{e.JobRole}</td>
                    <td className="py-2.5 pr-4 text-slate-400 text-xs">{e.Department}</td>
                    <td className="py-2.5 pr-4">
                      <span className="text-red-400 font-semibold text-xs">
                        {(e.attrition_risk_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-2.5">
                      <span className="text-amber-400 font-semibold text-xs">{e.tasks_assigned}/5</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
        <button
          onClick={() => onNavigate('recommendations')}
          className="flex items-center justify-between p-4 bg-teal-500/10 border border-teal-500/20 rounded-xl hover:bg-teal-500/15 transition-all group"
        >
          <div className="text-left">
            <p className="text-teal-400 font-semibold text-sm">Get a Recommendation</p>
            <p className="text-slate-500 text-xs mt-0.5">Pick a task and see who should own it</p>
          </div>
          <ArrowRight size={16} className="text-teal-500 group-hover:translate-x-1 transition-transform" />
        </button>
        <button
          onClick={() => onNavigate('team')}
          className="flex items-center justify-between p-4 bg-[#0f172a] border border-[#1e293b] rounded-xl hover:border-slate-600 transition-all group"
        >
          <div className="text-left">
            <p className="text-white font-semibold text-sm">Browse Team</p>
            <p className="text-slate-500 text-xs mt-0.5">Full risk and workload breakdown</p>
          </div>
          <ArrowRight size={16} className="text-slate-500 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  )
}
