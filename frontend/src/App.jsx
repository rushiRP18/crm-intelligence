import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import InboxPage from './pages/InboxPage'
import ThreadPage from './pages/ThreadPage'
import AnalyticsPage from './pages/AnalyticsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/inbox" replace />} />
        <Route path="inbox" element={<InboxPage />} />
        <Route path="thread/:threadId" element={<ThreadPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  )
}

export default App
