import { useEffect, useState, useMemo } from 'react'
import { Search, ArrowUpDown, AlertTriangle } from 'lucide-react'
import { fetchTeamOverview } from '../api'
import { Card, StatCard, Badge, ScoreBar, Spinner, ErrorMsg } from '../components/UI'

function riskVariant(score) {
  if (score >= 0.6) return 'red'
  if (score >= 0.4) return 'amber'
  return 'green'
}

function taskVariant(n) {
  if (n >= 4) return 'red'
  if (n >= 3) return 'amber'
  return 'green'
}

export default function TeamOverview() {
  const [team, setTeam]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [search, setSearch]   = useState('')
  const [sortKey, setSortKey] = useState('tasks_assigned')
  const [sortDir, setSortDir] = useState('desc')
  const [filter, setFilter]   = useState('all')

  useEffect(() => {
    fetchTeamOverview()
      .then(setTeam)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  function toggleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const filtered = useMemo(() => {
    let rows = team

    if (filter === 'danger') rows = rows.filter(e => e.attrition_risk_score >= 0.6 && e.tasks_assigned >= 4)
    else if (filter === 'risk') rows = rows.filter(e => e.attrition_risk_score >= 0.6)
    else if (filter === 'overloaded') rows = rows.filter(e => e.tasks_assigned >= 4)

    if (search.trim()) {
      const q = search.trim().toLowerCase()
      rows = rows.filter(e =>
        e.JobRole?.toLowerCase().includes(q) ||
        e.Department?.toLowerCase().includes(q) ||
        String(e.EmployeeNumber).includes(q) ||
        (e.OverTime?.toLowerCase() ?? '').includes(q)
      )
    }

    return [...rows].sort((a, b) => {
      const av = a[sortKey] ?? 0, bv = b[sortKey] ?? 0
      return sortDir === 'asc' ? av - bv : bv - av
    })
  }, [team, search, sortKey, sortDir, filter])

  if (loading) return <div className="p-8"><Spinner /></div>
  if (error)   return <div className="p-8"><ErrorMsg message={`Cannot reach backend: ${error}`} /></div>

  const highRisk   = team.filter(e => e.attrition_risk_score >= 0.6).length
  const overloaded = team.filter(e => e.tasks_assigned >= 4).length
  const danger     = team.filter(e => e.attrition_risk_score >= 0.6 && e.tasks_assigned >= 4).length

  const SortBtn = ({ col }) => {
    const active = sortKey === col
    return (
      <button onClick={() => toggleSort(col)} className={`ml-1 transition-colors ${active ? 'text-teal-400' : 'text-slate-600 hover:text-teal-400'}`}>
        {active ? (sortDir === 'asc' ? '↑' : '↓') : <ArrowUpDown size={11} />}
      </button>
    )
  }

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Team Overview</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Spot the default assignees — employees quietly accumulating workload and burnout risk.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Employees" value={team.length} />
        <StatCard label="Elevated Risk" value={highRisk} sub="≥ 60%" accent />
        <StatCard label="Near Capacity" value={overloaded} sub="≥ 4 tasks" />
        <StatCard label="Danger Zone" value={danger} sub="both conditions" danger />
      </div>

      {/* Filters & search */}
      <Card className="mb-4">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-48">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by role, department, or ID…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-[#0a0f1e] border border-[#334155] text-slate-200 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-teal-500/50 placeholder:text-slate-600"
            />
          </div>
          <div className="flex gap-2">
            {[
              { id: 'all',       label: 'All' },
              { id: 'danger',    label: '🚨 Danger Zone' },
              { id: 'risk',      label: '🔴 High Risk' },
              { id: 'overloaded',label: '⚠️ Overloaded' },
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setFilter(f.id)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all
                  ${filter === f.id
                    ? 'bg-teal-500/15 border-teal-500/30 text-teal-400'
                    : 'border-[#334155] text-slate-400 hover:text-slate-200 hover:border-slate-500'
                  }`}
              >
                {f.label}
              </button>
            ))}
          </div>
          <p className="text-slate-600 text-xs ml-auto">{filtered.length} employees</p>
        </div>
      </Card>

      {/* Table */}
      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-[#1e293b]">
              <tr>
                {[
                  { label: 'Employee', key: 'EmployeeNumber' },
                  { label: 'Role', key: 'JobRole' },
                  { label: 'Department', key: 'Department' },
                  { label: 'Attrition Risk', key: 'attrition_risk_score' },
                  { label: 'Tasks', key: 'tasks_assigned' },
                  { label: 'Overtime', key: 'OverTime' },
                ].map(({ label, key }) => (
                  <th key={key} className="text-left text-xs font-medium text-slate-500 uppercase tracking-wider px-4 py-3">
                    {label}<SortBtn col={key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]">
              {filtered.map(e => {
                const isDanger = e.attrition_risk_score >= 0.6 && e.tasks_assigned >= 4
                return (
                  <tr
                    key={e.EmployeeNumber}
                    className={`transition-colors hover:bg-[#1e293b]/60
                      ${isDanger ? 'bg-red-500/5' : ''}`}
                  >
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">
                      #{e.EmployeeNumber}
                      {isDanger && <AlertTriangle size={11} className="inline ml-1.5 text-red-400" />}
                    </td>
                    <td className="px-4 py-3 text-white text-xs font-medium">{e.JobRole}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{e.Department}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Badge variant={riskVariant(e.attrition_risk_score)}>
                          {(e.attrition_risk_score * 100).toFixed(0)}%
                        </Badge>
                        <div className="w-16">
                          <ScoreBar value={e.attrition_risk_score} color={e.attrition_risk_score >= 0.6 ? 'red' : e.attrition_risk_score >= 0.4 ? 'amber' : 'emerald'} />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Badge variant={taskVariant(e.tasks_assigned)}>
                          {e.tasks_assigned}/5
                        </Badge>
                        <div className="w-16">
                          <ScoreBar value={e.tasks_assigned} max={5} color={e.tasks_assigned >= 4 ? 'red' : e.tasks_assigned >= 3 ? 'amber' : 'emerald'} />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {e.OverTime === 'Yes'
                        ? <span className="inline-flex items-center gap-1 text-xs text-amber-400">⚡ Yes</span>
                        : <span className="text-xs text-slate-600">No</span>
                      }
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-slate-600 text-sm">No employees match the current filter.</div>
          )}
        </div>
      </Card>
    </div>
  )
}
