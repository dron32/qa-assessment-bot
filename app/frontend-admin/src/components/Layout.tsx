import { Outlet, Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Button } from './ui/button'
import { 
  Users, 
  FileText, 
  Calendar, 
  Shield,
  Globe,
  LogOut
} from 'lucide-react'

const navigation = [
  { name: 'competencies', href: '/competencies', icon: FileText },
  { name: 'templates', href: '/templates', icon: FileText },
  { name: 'cycles', href: '/cycles', icon: Calendar },
  { name: 'users', href: '/users', icon: Users },
  { name: 'audit', href: '/audit', icon: Shield },
]

export default function Layout() {
  const { t, i18n } = useTranslation()
  const location = useLocation()

  const toggleLanguage = () => {
    i18n.changeLanguage(i18n.language === 'en' ? 'ru' : 'en')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-sm border-r">
        <div className="p-6">
          <h1 className="text-xl font-bold text-gray-900">QA Assessment</h1>
          <p className="text-sm text-gray-500">Admin Panel</p>
        </div>
        
        <nav className="px-4 pb-4">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-md mb-1 ${
                  isActive
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <item.icon className="mr-3 h-5 w-5" />
                {t(`nav.${item.name}`)}
              </Link>
            )
          })}
        </nav>

        <div className="absolute bottom-4 left-4 right-4">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className="flex-1"
            >
              <Globe className="h-4 w-4 mr-2" />
              {i18n.language === 'en' ? 'RU' : 'EN'}
            </Button>
            <Button variant="outline" size="sm">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
