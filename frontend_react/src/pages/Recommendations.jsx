import { useEffect, useState } from 'react'
import { Sparkles, AlertTriangle, ChevronDown } from 'lucide-react'
import { fetchTasks, fetchRecommendations } from '../api'
import { Card, Badge, ScoreBar, Spinner, ErrorMsg } from '../components/UI'

function riskVariant(score) {
  if (score >= 0.6) return 'red'
  if (score >= 0.4) return 'amber'
  return 'green'
}

function urgencyLabel(u) {
  return ['', 'Low', 'Medium', 'High'][u] ?? u
}

function CandidateCard({ c, rank }) {
  const isTop = rank === 1
  const wasBypassed = c.skill_rank === 1 && rank !== 1
  const penalised = c.risk_penalty > 0

  return (
    <div className={`relative bg-[#0a0f1e] border rounded-xl p-5 transition-all
      ${isTop ? 'border-teal-500/40 ring-1 ring-teal-500/20' : 'border-[#1e293b]'}`}>
      {isTop && (
        <div className="absolute -top-3 left-4">
          <span className="bg-teal-500 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">
            ✓ Recommended
          </span>
        </div>
      )}
      {wasBypassed && (
        <div className="absolute -top-3 left-4">
          <span className="bg-amber-500/80 text-white text-xs font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
            <AlertTriangle size={10} /> Top skill match — bypassed
          </span>
        </div>
      )}

      <div className="mt-1">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-white font-semibold text-sm">{c.JobRole}</p>
            <p className="text-slate-500 text-xs">{c.Department} · #{c.EmployeeNumber}</p>
          </div>
          <Badge variant={riskVariant(c.attrition_risk_score)}>
            {(c.attrition_risk_score * 100).toFixed(0)}% risk
          </Badge>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-500">Skill fit</span>
              <span className="text-white font-medium">{(c.skill_fit_score * 100).toFixed(0)}%</span>
            </div>
            <ScoreBar value={c.skill_fit_score} color="teal" />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-500">Availability</span>
              <span className="text-white font-medium">{5 - c.tasks_assigned}/5 slots free</span>
            </div>
            <ScoreBar value={5 - c.tasks_assigned} max={5} color="emerald" />
          </div>

          {penalised && (
            <div className="flex items-center gap-1.5 bg-red-500/5 border border-red-500/15 rounded-lg px-3 py-2 mt-2">
              <AlertTriangle size={12} className="text-red-400 flex-shrink-0" />
              <p className="text-red-400 text-xs">Risk penalty applied: −{c.risk_penalty.toFixed(3)}</p>
            </div>
          )}

          <div className="pt-2 border-t border-[#1e293b] flex justify-between text-xs">
            <span className="text-slate-500">Final score</span>
            <span className={`font-bold ${isTop ? 'text-teal-400' : 'text-slate-300'}`}>
              {c.final_score.toFixed(3)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Recommendations() {
  const [tasks, setTasks]           = useState([])
  const [selectedTask, setSelected] = useState(null)
  const [result, setResult]         = useState(null)
  const [loading, setLoading]       = useState(false)
  const [tasksLoading, setTL]       = useState(true)
  const [error, setError]           = useState(null)
  const [showBreakdown, setShowBD]  = useState(false)

  useEffect(() => {
    fetchTasks()
      .then(t => { setTasks(t); setSelected(t[0] ?? null) })
      .catch(e => setError(e.message))
      .finally(() => setTL(false))
  }, [])

  async function getRecommendation() {
    if (!selectedTask) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const data = await fetchRecommendations(selectedTask.task_id)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (tasksLoading) return <div className="p-8"><Spinner /></div>

  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Task Recommendations</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Select an open task to see who should own it — balancing skill fit with workload sustainability.
        </p>
      </div>

      {/* Task selector */}
      <Card className="mb-6">
        <h2 className="text-white font-semibold text-sm mb-4">Select a Task</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 mb-5 max-h-64 overflow-y-auto pr-1">
          {tasks.map(t => (
            <button
              key={t.task_id}
              onClick={() => { setSelected(t); setResult(null) }}
              className={`text-left p-3 rounded-lg border text-xs transition-all
                ${selectedTask?.task_id === t.task_id
                  ? 'border-teal-500/40 bg-teal-500/10 text-teal-300'
                  : 'border-[#1e293b] text-slate-400 hover:border-slate-600 hover:text-slate-200'
                }`}
            >
              <p className="font-medium text-[11px] text-slate-500 mb-0.5">[{t.task_id}]</p>
              <p className="leading-tight">{t.title}</p>
            </button>
          ))}
        </div>

        {selectedTask && (
          <div className="border-t border-[#1e293b] pt-4">
            <div className="flex flex-wrap gap-4 mb-4">
              <div>
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Required skills</p>
                <div className="flex flex-wrap gap-1">
                  {selectedTask.required_skills.map(s => (
                    <span key={s} className="bg-[#1e293b] text-slate-300 text-xs px-2 py-0.5 rounded">{s}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Urgency</p>
                <Badge variant={['', 'green', 'amber', 'red'][selectedTask.urgency]}>
                  {urgencyLabel(selectedTask.urgency)}
                </Badge>
              </div>
              <div>
                <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Effort</p>
                <p className="text-white text-sm font-medium">{selectedTask.effort} hrs</p>
              </div>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">{selectedTask.description}</p>
          </div>
        )}

        <button
          onClick={getRecommendation}
          disabled={!selectedTask || loading}
          className="mt-5 w-full flex items-center justify-center gap-2 bg-teal-500 hover:bg-teal-400 disabled:bg-teal-500/30 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-lg transition-all text-sm"
        >
          {loading ? (
              <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analysing — calling AI, may take 5–10s…</>
            ) : (
              <><Sparkles size={15} /> Get Recommendation</>
            )}
        </button>
      </Card>

      {error && <ErrorMsg message={error} />}

      {result && (
        <>
          {/* Displacement warning */}
          {result.displaced_top_match && (
            <div className="flex items-start gap-3 bg-amber-500/10 border border-amber-500/25 rounded-xl p-4 mb-5">
              <AlertTriangle size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-amber-400 font-semibold text-sm">Top skill match bypassed</p>
                <p className="text-amber-300/70 text-xs mt-0.5">
                  The strongest technical fit was not recommended — they carry elevated attrition risk and are near their workload ceiling. Assigning them would compound an existing risk.
                </p>
              </div>
            </div>
          )}

          {/* Candidate cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            {result.candidates.map((c, i) => (
              <CandidateCard key={c.EmployeeNumber} c={c} rank={i + 1} />
            ))}
          </div>

          {/* Explanation */}
          <Card className="mb-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={14} className="text-teal-400" />
              <h2 className="text-white font-semibold text-sm">AI Recommendation</h2>
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">{result.explanation}</p>
          </Card>

          {/* Score breakdown (collapsible) */}
          <button
            onClick={() => setShowBD(!showBreakdown)}
            className="flex items-center gap-1.5 text-slate-500 hover:text-slate-300 text-xs transition-colors mb-2"
          >
            <ChevronDown size={14} className={`transition-transform ${showBreakdown ? 'rotate-180' : ''}`} />
            {showBreakdown ? 'Hide' : 'Show'} score breakdown
          </button>
          {showBreakdown && (
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#1e293b]">
                      {['Employee', 'Role', 'Skill Fit', 'Availability', 'Risk Penalty', 'Final Score', 'Skill Rank', 'Final Rank'].map(h => (
                        <th key={h} className="text-left text-slate-500 uppercase tracking-wider font-medium pb-2 pr-3">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e293b]">
                    {result.candidates.map(c => (
                      <tr key={c.EmployeeNumber}>
                        <td className="py-2 pr-3 text-slate-400 font-mono">#{c.EmployeeNumber}</td>
                        <td className="py-2 pr-3 text-white">{c.JobRole}</td>
                        <td className="py-2 pr-3 text-teal-400">{(c.skill_fit_score * 100).toFixed(0)}%</td>
                        <td className="py-2 pr-3 text-emerald-400">{(c.availability_bonus * 100).toFixed(0)}%</td>
                        <td className="py-2 pr-3 text-red-400">{c.risk_penalty > 0 ? `−${c.risk_penalty.toFixed(3)}` : '—'}</td>
                        <td className="py-2 pr-3 text-white font-bold">{c.final_score.toFixed(3)}</td>
                        <td className="py-2 pr-3 text-slate-400">#{c.skill_rank}</td>
                        <td className="py-2 text-slate-400">#{c.final_rank}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
