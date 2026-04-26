import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import Stock from './pages/Stock'
import Trucks from './pages/Trucks'
import Shipments from './pages/Shipments'

const queryClient = new QueryClient()

const NAV_LINKS = [
  { to: '/', label: 'Dashboard' },
  { to: '/stock', label: 'Stock' },
  { to: '/trucks', label: 'Trucks' },
  { to: '/shipments', label: 'Shipments' },
]

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex min-h-screen">
          <aside className="w-48 shrink-0 bg-gray-900 text-white">
            <div className="px-4 py-5 text-lg font-bold tracking-tight">Shipping Mgr</div>
            <nav className="mt-2 flex flex-col gap-0.5 px-2">
              {NAV_LINKS.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `rounded px-3 py-2 text-sm transition-colors ${
                      isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
                    }`
                  }
                >
                  {label}
                </NavLink>
              ))}
            </nav>
          </aside>
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stock" element={<Stock />} />
              <Route path="/trucks" element={<Trucks />} />
              <Route path="/shipments" element={<Shipments />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
