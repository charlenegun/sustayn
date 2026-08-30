import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Recommendations from './pages/Recommendations'
import TeamOverview from './pages/TeamOverview'

export default function App() {
  const [page, setPage] = useState('dashboard')

  const pages = {
    dashboard: <Dashboard onNavigate={setPage} />,
    recommendations: <Recommendations />,
    team: <TeamOverview />,
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0f1e]">
      <Sidebar current={page} onNavigate={setPage} />
      <main className="flex-1 overflow-y-auto">
        {pages[page]}
      </main>
    </div>
  )
}
