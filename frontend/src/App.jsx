import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import ComplaintForm from './components/ComplaintForm'
import Dashboard from './components/Dashboard'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main">
        <Routes>
          <Route path="/"          element={<ComplaintForm />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
