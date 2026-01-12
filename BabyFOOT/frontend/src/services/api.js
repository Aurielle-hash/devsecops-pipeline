import axios from 'axios'
import { apm } from '../apm'

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8085/api'

// Create axios instance with APM instrumentation
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
})

// Add request interceptor for APM tracing
api.interceptors.request.use(
    (config) => {
        // Start APM span for API calls
        const span = apm.startSpan(`${config.method?.toUpperCase()} ${config.url}`, 'http')
        config.metadata = { span }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Add response interceptor for APM tracing
api.interceptors.response.use(
    (response) => {
        // End APM span
        if (response.config.metadata?.span) {
            response.config.metadata.span.end()
        }
        return response
    },
    (error) => {
        // End APM span with error
        if (error.config?.metadata?.span) {
            error.config.metadata.span.end()
        }
        apm.captureError(error)
        return Promise.reject(error)
    }
)

// Players API
export const playersAPI = {
    getAll: () => api.get('/players'),
    getById: (id) => api.get(`/players/${id}`),
    getByName: (name) => api.get(`/players/name/${name}`),
    create: (player) => api.post('/players', player),
    update: (id, player) => api.put(`/players/${id}`, player),
    delete: (id) => api.delete(`/players/${id}`)
}

// Matches API
export const matchesAPI = {
    getAll: () => api.get('/matches'),
    getById: (id) => api.get(`/matches/${id}`),
    getByPlayer: (playerName) => api.get(`/matches/player/${playerName}`),
    getActive: () => api.get('/matches/active'),
    create: (match) => api.post('/matches', match),
    updateScore: (id, score1, score2) => api.put(`/matches/${id}/score`, { score1, score2 }),
    finish: (id) => api.put(`/matches/${id}/finish`),
    delete: (id) => api.delete(`/matches/${id}`)
}

export default api