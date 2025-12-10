import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from './components/ui/Toaster'
import Layout from './components/layout/Layout'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'
import GraphExplorer from './pages/GraphExplorer'
import Simulation from './pages/Simulation'
import Playground from './pages/Playground'
import Alerts from './pages/Alerts'
import Leaderboard from './pages/Leaderboard'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing page - no layout */}
        <Route path="/" element={<LandingPage />} />

        {/* Dashboard routes with layout */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/explorer" element={<GraphExplorer />} />
          <Route path="/simulation" element={<Simulation />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}

export default App
