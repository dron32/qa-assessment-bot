import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Plus, Edit, Trash2 } from 'lucide-react'

interface Template {
  id: number
  competency_id: number
  language: string
  content: string
  version: number
}

// Заглушка API
const mockTemplates: Template[] = [
  { id: 1, competency_id: 1, language: 'ru', content: 'Пример шаблона для аналитического мышления', version: 1 },
  { id: 2, competency_id: 2, language: 'ru', content: 'Пример шаблона для баг-репортов', version: 1 },
]

export default function Templates() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ competency_id: 1, language: 'ru', content: '' })

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => Promise.resolve(mockTemplates),
  })

  const createMutation = useMutation({
    mutationFn: (data: Omit<Template, 'id' | 'version'>) => Promise.resolve({ id: Date.now(), ...data, version: 1 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setIsCreating(false)
      setFormData({ competency_id: 1, language: 'ru', content: '' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: Template) => Promise.resolve({ id, ...data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setEditingId(null)
      setFormData({ competency_id: 1, language: 'ru', content: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => Promise.resolve(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingId) {
      updateMutation.mutate({
        id: editingId,
        competency_id: formData.competency_id,
        language: formData.language,
        content: formData.content,
        version: 1,
      })
    } else {
      createMutation.mutate({
        competency_id: formData.competency_id,
        language: formData.language,
        content: formData.content,
      })
    }
  }

  const startEdit = (template: Template) => {
    setEditingId(template.id)
    setFormData({
      competency_id: template.competency_id,
      language: template.language,
      content: template.content,
    })
  }

  if (isLoading) return <div>{t('common.loading')}</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{t('templates.title')}</h1>
        <Button onClick={() => setIsCreating(true)}>
          <Plus className="h-4 w-4 mr-2" />
          {t('templates.create')}
        </Button>
      </div>

      {/* Форма создания/редактирования */}
      {(isCreating || editingId) && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingId ? t('templates.edit') : t('templates.create')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">{t('templates.competency')}</label>
                <Input
                  type="number"
                  value={formData.competency_id}
                  onChange={(e) => setFormData({ ...formData, competency_id: parseInt(e.target.value) })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('templates.language')}</label>
                <Input
                  value={formData.language}
                  onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                  placeholder="ru"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">{t('templates.content')}</label>
                <textarea
                  className="w-full p-2 border rounded-md"
                  rows={4}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="Содержание шаблона"
                  required
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
                    setFormData({ competency_id: 1, language: 'ru', content: '' })
                  }}
                >
                  {t('common.cancel')}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Список шаблонов */}
      <div className="grid gap-4">
        {templates.map((template) => (
          <Card key={template.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">Competency {template.competency_id}</h3>
                  <p className="text-sm text-gray-500">{template.language} v{template.version}</p>
                  <p className="text-sm text-gray-600 mt-1">{template.content}</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => startEdit(template)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => deleteMutation.mutate(template.id)}
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
