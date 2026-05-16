import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import LoginPage from './domains/auth/pages/LoginPage'
import RegisterPage from './domains/auth/pages/RegisterPage'
import IntegracoesPage from './domains/auth/pages/IntegracoesPage'
import ConfiguracoesPage from './domains/auth/pages/ConfiguracoesPage'
import { PrivateRoute } from './domains/auth/components/PrivateRoute'
import { AppShell } from './components/templates/AppShell'
import EntradasPage from './domains/finance/pages/EntradasPage'
import SaidasPage from './domains/finance/pages/SaidasPage'
import ParcelamentosPage from './domains/finance/pages/ParcelamentosPage'
import CategoriasPage from './domains/finance/pages/CategoriasPage'
import ExtratoPage from './domains/finance/pages/ExtratoPage'
import DashboardPage from './domains/finance/pages/DashboardPage'

function App() {
  const location = useLocation()
  const isAuthRoute =
    location.pathname === '/login' || location.pathname === '/register'

  if (isAuthRoute) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    )
  }

  return (
    <PrivateRoute>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/entradas" element={<EntradasPage />} />
          <Route path="/saidas" element={<SaidasPage />} />
          <Route path="/parcelamentos" element={<ParcelamentosPage />} />
          <Route path="/categorias" element={<CategoriasPage />} />
          <Route path="/extrato" element={<ExtratoPage />} />
          <Route path="/integracoes" element={<IntegracoesPage />} />
          <Route path="/configuracoes" element={<ConfiguracoesPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </PrivateRoute>
  )
}

export default App
