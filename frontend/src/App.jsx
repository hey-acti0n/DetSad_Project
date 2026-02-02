import { Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import './Admin.css'
import GroupSelect from './pages/GroupSelect'
import Play from './pages/Play'
import OurTree from './pages/OurTree'
import AdminLogin from './pages/AdminLogin'
import AdminPanel from './pages/AdminPanel'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<GroupSelect />} />
      <Route path="/play/:groupId" element={<Play />} />
      <Route path="/our-tree" element={<OurTree />} />
      <Route path="/admin-login" element={<AdminLogin />} />
      <Route path="/admin" element={<AdminPanel />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
