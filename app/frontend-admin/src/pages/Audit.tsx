import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Search } from 'lucide-react'

interface AuditLog {
  id: number
  user_id?: number
  action: string
  payload?: any
  created_at: string
}

// Заглушка API
const mockAuditLogs: AuditLog[] = [
  { id: 1, user_id: 1, action: 'create_competency', payload: { key: 'analytical_thinking' }, created_at: '2024-01-15T10:30:00Z' },
  { id: 2, user_id: 2, action: 'update_template', payload: { template_id: 1 }, created_at: '2024-01-15T11:15:00Z' },
  { id: 3, user_id: 1, action: 'delete_user', payload: { user_id: 3 }, created_at: '2024-01-15T12:00:00Z' },
  { id: 4, user_id: 2, action: 'create_cycle', payload: { title: 'Q1 2025 Review' }, created_at: '2024-01-15T13:45:00Z' },
]

export default function Audit() {
  const { t } = useTranslation()
  const [searchTerm, setSearchTerm] = useState('')

  const { data: auditLogs = [], isLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => Promise.resolve(mockAuditLogs),
  })

  const filteredLogs = auditLogs.filter(log =>
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.payload?.toString().toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) return <div>{t('common.loading')}</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{t('audit.title')}</h1>
      </div>

      {/* Поиск */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder={t('common.search')}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Список логов */}
      <div className="space-y-4">
        {filteredLogs.map((log) => (
          <Card key={log.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold">{log.action}</h3>
                    {log.user_id && (
                      <span className="text-sm text-gray-500">User {log.user_id}</span>
                    )}
                  </div>
                  {log.payload && (
                    <div className="bg-gray-50 p-2 rounded text-sm">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(log.payload, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
                <div className="text-sm text-gray-500 ml-4">
                  {formatDate(log.created_at)}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredLogs.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-gray-500">No audit logs found</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
