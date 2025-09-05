import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Plus, Edit, Trash2 } from 'lucide-react'

interface Competency {
  id: number
  key: string
  title: string
  description?: string
  is_active: boolean
}

// Заглушка API
const mockCompetencies: Competency[] = [
  { id: 1, key: 'analytical_thinking', title: 'Аналитическое мышление', description: 'Способность анализировать проблемы', is_active: true },
  { id: 2, key: 'bug_reports', title: 'Качество баг-репортов', description: 'Навыки написания качественных баг-репортов', is_active: true },
  { id: 3, key: 'documentation', title: 'Работа с документацией', description: 'Умение работать с тестовой документацией', is_active: true },
]

export default function Competencies() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ key: '', title: '', description: '' })

  const { data: competencies = [], isLoading } = useQuery({
    queryKey: ['competencies'],
    queryFn: () => Promise.resolve(mockCompetencies),
  })

  const createMutation = useMutation({
    mutationFn: (data: Omit<Competency, 'id'>) => Promise.resolve({ id: Date.now(), ...data, is_active: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competencies'] })
      setIsCreating(false)
      setFormData({ key: '', title: '', description: '' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: Competency) => Promise.resolve({ id, ...data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competencies'] })
      setEditingId(null)
      setFormData({ key: '', title: '', description: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => Promise.resolve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competencies'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId) {
      updateMutation.mutate({
        id: editingId,
        key: formData.key,
        title: formData.title,
        description: formData.description,
        is_active: true,
      })
    } else {
      createMutation.mutate({
        key: formData.key,
        title: formData.title,
        description: formData.description,
        is_active: true,
      })
    }
  }

  const startEdit = (competency: Competency) => {
    setEditingId(competency.id)
    setFormData({
      key: competency.key,
      title: competency.title,
      description: competency.description || '',
    })
  }

  if (isLoading) return <div>{t('common.loading')}</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{t('competencies.title')}</h1>
        <Button onClick={() => setIsCreating(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('competencies.create')}
        </Button>
      </div>

      {/* Форма создания/редактирования */}
      {(isCreating || editingId) && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingId ? t('competencies.edit') : t('competencies.create')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">{t('competencies.key')}</label>
                <Input
                  value={formData.key}
                  onChange={(e) => setFormData({ ...formData, key: e.target.value })}
                  placeholder="analytical_thinking"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('competencies.title')}</label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Аналитическое мышление"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('competencies.description')}</label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Описание компетенции"
                />
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
                    setFormData({ key: '', title: '', description: '' })
                  }}
                >
                  {t('common.cancel')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Список компетенций */}
      <div className="grid gap-4">
        {competencies.map((competency) => (
          <Card key={competency.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{competency.title}</h3>
                  <p className="text-sm text-gray-500">{competency.key}</p>
                  {competency.description && (
                    <p className="text-sm text-gray-600 mt-1">{competency.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => startEdit(competency)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteMutation.mutate(competency.id)}
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
