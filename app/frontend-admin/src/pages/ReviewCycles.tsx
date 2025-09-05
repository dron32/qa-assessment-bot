import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Plus, Edit, Trash2 } from 'lucide-react'
import { reviewCyclesApi, type ReviewCycle } from '../lib/api'

export default function ReviewCycles() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ title: '', starts_at: '', ends_at: '', status: 'planned' })

  const { data: cyclesData, isLoading } = useQuery({
    queryKey: ['cycles'],
    queryFn: reviewCyclesApi.getAll,
  })

  const cycles = cyclesData?.cycles || []

  const createMutation = useMutation({
    mutationFn: (data: { title: string; start_date?: string; end_date?: string }) => 
      reviewCyclesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
      setIsCreating(false)
      setFormData({ title: '', starts_at: '', ends_at: '', status: 'planned' })
    },
    onError: (error) => {
      console.error('Failed to create review cycle:', error)
      alert(`Ошибка создания цикла ревью: ${error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number; title: string; start_date?: string; end_date?: string }) => 
      reviewCyclesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
      setEditingId(null)
      setFormData({ title: '', starts_at: '', ends_at: '', status: 'planned' })
    },
    onError: (error) => {
      console.error('Failed to update review cycle:', error)
      alert(`Ошибка обновления цикла ревью: ${error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => reviewCyclesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
    },
    onError: (error) => {
      console.error('Failed to delete review cycle:', error)
      alert(`Ошибка удаления цикла ревью: ${error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Проверяем валидность формы
    if (!formData.title.trim()) {
      alert('Пожалуйста, заполните название цикла ревью')
      return
    }
    
    if (editingId) {
      updateMutation.mutate({
        id: editingId,
        title: formData.title,
        start_date: formData.starts_at || undefined,
        end_date: formData.ends_at || undefined,
      })
    } else {
      createMutation.mutate({
        title: formData.title,
        start_date: formData.starts_at || undefined,
        end_date: formData.ends_at || undefined,
      })
    }
  }

  const startEdit = (cycle: ReviewCycle) => {
    setEditingId(cycle.id)
    setFormData({
      title: cycle.title,
      starts_at: cycle.start_date || '',
      ends_at: cycle.end_date || '',
      status: 'planned', // Убираем status, так как его нет в API
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
                    {cycle.start_date && cycle.end_date 
                      ? `${cycle.start_date} - ${cycle.end_date}`
                      : 'Даты не указаны'
                    }
                  </p>
                  <span className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                    cycle.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {cycle.is_active ? 'Активный' : 'Неактивный'}
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
