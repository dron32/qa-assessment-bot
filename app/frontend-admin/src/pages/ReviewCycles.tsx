import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Plus, Edit, Trash2 } from 'lucide-react'

interface ReviewCycle {
  id: number
  title: string
  starts_at?: string
  ends_at?: string
  status?: string
}

// Заглушка API
const mockCycles: ReviewCycle[] = [
  { id: 1, title: 'Q4 2024 Review', starts_at: '2024-10-01', ends_at: '2024-12-31', status: 'active' },
  { id: 2, title: 'Q1 2025 Review', starts_at: '2025-01-01', ends_at: '2025-03-31', status: 'planned' },
]

export default function ReviewCycles() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ title: '', starts_at: '', ends_at: '', status: 'planned' })

  const { data: cycles = [], isLoading } = useQuery({
    queryKey: ['cycles'],
    queryFn: () => Promise.resolve(mockCycles),
  })

  const createMutation = useMutation({
    mutationFn: (data: Omit<ReviewCycle, 'id'>) => Promise.resolve({ id: Date.now(), ...data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
      setIsCreating(false)
      setFormData({ title: '', starts_at: '', ends_at: '', status: 'planned' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: ReviewCycle) => Promise.resolve({ id, ...data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
      setEditingId(null)
      setFormData({ title: '', starts_at: '', ends_at: '', status: 'planned' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => Promise.resolve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId) {
      updateMutation.mutate({
        id: editingId,
        title: formData.title,
        starts_at: formData.starts_at || undefined,
        ends_at: formData.ends_at || undefined,
        status: formData.status,
      })
    } else {
      createMutation.mutate({
        title: formData.title,
        starts_at: formData.starts_at || undefined,
        ends_at: formData.ends_at || undefined,
        status: formData.status,
      })
    }
  }

  const startEdit = (cycle: ReviewCycle) => {
    setEditingId(cycle.id)
    setFormData({
      title: cycle.title,
      starts_at: cycle.starts_at || '',
      ends_at: cycle.ends_at || '',
      status: cycle.status || 'planned',
    })
  }

  if (isLoading) return <div>{t('common.loading')}</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{t('cycles.title')}</h1>
        <Button onClick={() => setIsCreating(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('cycles.create')}
        </Button>
      </div>

      {/* Форма создания/редактирования */}
      {(isCreating || editingId) && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingId ? t('cycles.edit') : t('cycles.create')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">{t('cycles.title')}</label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Q4 2024 Review"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">{t('cycles.startsAt')}</label>
                  <Input
                    type="date"
                    value={formData.starts_at}
                    onChange={(e) => setFormData({ ...formData, starts_at: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">{t('cycles.endsAt')}</label>
                  <Input
                    type="date"
                    value={formData.ends_at}
                    onChange={(e) => setFormData({ ...formData, ends_at: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('cycles.status')}</label>
                <select
                  className="w-full p-2 border rounded-md"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="planned">Planned</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                  {t('common.save')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsCreating(false)
                    setEditingId(null)
                    setFormData({ title: '', starts_at: '', ends_at: '', status: 'planned' })
                  }}
                >
                  {t('common.cancel')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Список циклов */}
      <div className="grid gap-4">
        {cycles.map((cycle) => (
          <Card key={cycle.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{cycle.title}</h3>
                  <p className="text-sm text-gray-500">
                    {cycle.starts_at && cycle.ends_at 
                      ? `${cycle.starts_at} - ${cycle.ends_at}`
                      : 'Даты не указаны'
                    }
                  </p>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                    cycle.status === 'active' ? 'bg-green-100 text-green-800' :
                    cycle.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {cycle.status}
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => startEdit(cycle)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteMutation.mutate(cycle.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
