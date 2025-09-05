import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Competencies from './pages/Competencies'
import Templates from './pages/Templates'
import ReviewCycles from './pages/ReviewCycles'
import Users from './pages/Users'
import Audit from './pages/Audit'

function App() {

  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/competencies" replace />} />
          <Route path="competencies" element={<Competencies />} />
          <Route path="templates" element={<Templates />} />
          <Route path="cycles" element={<ReviewCycles />} />
          <Route path="users" element={<Users />} />
          <Route path="audit" element={<Audit />} />
        </Route>
      </Routes>
    </div>
  )
}

export default App
