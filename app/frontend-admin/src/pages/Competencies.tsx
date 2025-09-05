import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Plus, Edit, Trash2 } from 'lucide-react'
import { competenciesApi, type Competency } from '../lib/api'

export default function Competencies() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ key: '', title: '', description: '' })

  const { data: competenciesData, isLoading } = useQuery({
    queryKey: ['competencies'],
    queryFn: competenciesApi.getAll,
  })

  const competencies = competenciesData?.competencies || []

  const createMutation = useMutation({
    mutationFn: (data: { key: string; title: string; description?: string }) => {
      console.log('Creating competency with data:', data)
      return competenciesApi.create(data)
    },
    onSuccess: (result) => {
      console.log('Competency created successfully:', result)
      queryClient.invalidateQueries({ queryKey: ['competencies'] })
      setIsCreating(false)
      setFormData({ key: '', title: '', description: '' })
    },
    onError: (error) => {
      console.error('Failed to create competency:', error)
      alert(`Ошибка создания компетенции: ${error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number; key: string; title: string; description?: string }) => 
      competenciesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competencies'] })
      setEditingId(null)
      setFormData({ key: '', title: '', description: '' })
    },
    onError: (error) => {
      console.error('Failed to update competency:', error)
      alert(`Ошибка обновления компетенции: ${error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => competenciesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competencies'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Form submitted:', { editingId, formData })
    
    // Проверяем валидность формы
    if (!formData.key.trim() || !formData.title.trim()) {
      console.error('Form validation failed: missing required fields')
      alert('Пожалуйста, заполните все обязательные поля')
      return
    }
    
    if (editingId) {
      console.log('Updating competency:', editingId)
      updateMutation.mutate({
        id: editingId,
        key: formData.key,
        title: formData.title,
        description: formData.description,
      })
    } else {
      console.log('Creating new competency')
      createMutation.mutate({
        key: formData.key,
        title: formData.title,
        description: formData.description,
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
            <form onSubmit={handleSubmit} className="space-y-4" onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                console.log('Ctrl+Enter pressed')
                handleSubmit(e)
              }
            }}>
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
                <Button 
                  type="submit" 
                  disabled={createMutation.isPending || updateMutation.isPending}
                  onClick={() => console.log('Save button clicked')}
                >
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
