const API_BASE_URL = 'http://localhost:8000/api'

// Типы данных
export interface Competency {
  id: number
  key: string
  title: string
  description?: string
  is_active: boolean
}

export interface Template {
  id: number
  competency_id: number
  language: string
  content: string
  version?: number
}

export interface User {
  id: number
  handle: string
  email: string
  role: string
}

export interface ReviewCycle {
  id: number
  title: string
  start_date?: string
  end_date?: string
  is_active: boolean
}

// API функции для компетенций
export const competenciesApi = {
  async getAll(): Promise<{ competencies: Competency[] }> {
    const response = await fetch(`${API_BASE_URL}/admin/competencies`, {
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to fetch competencies')
    }
    return response.json()
  },

  async create(data: { key: string; title: string; description?: string }): Promise<Competency> {
    console.log('API: Creating competency:', data)
    const response = await fetch(`${API_BASE_URL}/admin/competencies`, {
      method: 'POST',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    console.log('API: Response status:', response.status)
    if (!response.ok) {
      const errorText = await response.text()
      console.error('API: Failed to create competency:', response.status, errorText)
      throw new Error(`Failed to create competency: ${response.status} ${errorText}`)
    }
    const result = await response.json()
    console.log('API: Created competency:', result)
    return result
  },

  async update(id: number, data: { key: string; title: string; description?: string }): Promise<Competency> {
    const response = await fetch(`${API_BASE_URL}/admin/competencies/${id}`, {
      method: 'PUT',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to update competency')
    }
    return response.json()
  },

  async delete(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/admin/competencies/${id}`, {
      method: 'DELETE',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to delete competency')
    }
  },
}

// API функции для шаблонов
export const templatesApi = {
  async getAll(): Promise<{ templates: Template[] }> {
    const response = await fetch(`${API_BASE_URL}/admin/templates`, {
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Failed to fetch templates:', response.status, errorText)
      throw new Error(`Failed to fetch templates: ${response.status} ${errorText}`)
    }
    return response.json()
  },

  async create(data: { competency_id: number; language: string; content: string }): Promise<Template> {
    console.log('API: Creating template:', data)
    const response = await fetch(`${API_BASE_URL}/admin/templates`, {
      method: 'POST',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    console.log('API: Template response status:', response.status)
    if (!response.ok) {
      const errorText = await response.text()
      console.error('API: Failed to create template:', response.status, errorText)
      throw new Error(`Failed to create template: ${response.status} ${errorText}`)
    }
    const result = await response.json()
    console.log('API: Created template:', result)
    return result
  },

  async update(id: number, data: { competency_id: number; language: string; content: string }): Promise<Template> {
    const response = await fetch(`${API_BASE_URL}/admin/templates/${id}`, {
      method: 'PUT',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to update template')
    }
    return response.json()
  },

  async delete(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/admin/templates/${id}`, {
      method: 'DELETE',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to delete template')
    }
  },
}

// API функции для пользователей
export const usersApi = {
  async getAll(): Promise<{ users: User[] }> {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to fetch users')
    }
    return response.json()
  },

  async create(data: { handle: string; email: string; role?: string }): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      method: 'POST',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to create user')
    }
    return response.json()
  },

  async update(id: number, data: { handle: string; email: string; role?: string }): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/admin/users/${id}`, {
      method: 'PUT',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to update user')
    }
    return response.json()
  },

  async delete(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/admin/users/${id}`, {
      method: 'DELETE',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to delete user')
    }
  },
}

// API функции для циклов ревью
export const reviewCyclesApi = {
  async getAll(): Promise<{ cycles: ReviewCycle[] }> {
    const response = await fetch(`${API_BASE_URL}/admin/review_cycles`, {
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to fetch review cycles')
    }
    return response.json()
  },

  async create(data: { title: string; start_date?: string; end_date?: string }): Promise<ReviewCycle> {
    const response = await fetch(`${API_BASE_URL}/admin/review_cycles`, {
      method: 'POST',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to create review cycle')
    }
    return response.json()
  },

  async update(id: number, data: { title: string; start_date?: string; end_date?: string }): Promise<ReviewCycle> {
    const response = await fetch(`${API_BASE_URL}/admin/review_cycles/${id}`, {
      method: 'PUT',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to update review cycle')
    }
    return response.json()
  },

  async delete(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/admin/review_cycles/${id}`, {
      method: 'DELETE',
      headers: {
        'X-User-Id': '1',
        'X-User-Role': 'admin',
      },
    })
    if (!response.ok) {
      throw new Error('Failed to delete review cycle')
    }
  },
}
