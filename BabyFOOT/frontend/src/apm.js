import { init as initApm } from '@elastic/apm-rum'

export const apm = initApm({
    serviceName: 'babyfoot-frontend',
    serverUrl: 'http://localhost:8200',
    environment: 'development',
    distributedTracingOrigins: ['http://localhost:8085'],
    capturePageLoad: true,
    debug: true
})

export default apm