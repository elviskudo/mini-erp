// Server middleware to proxy /api requests to backend
// This fixes the duplicate Transfer-Encoding header issue with nitro proxy

export default defineEventHandler(async (event) => {
    const requestUrl = getRequestURL(event)
    const path = requestUrl.pathname

    // Only handle /api routes, but EXCLUDE internal Nuxt paths like /_nuxt_icon
    if (!path.startsWith('/api/') || path.startsWith('/api/_nuxt')) {
        return
    }

    const backendUrl = 'http://backend_api:8000'
    const targetPath = path.replace('/api/', '/')
    // Include query params in the target URL
    const queryString = requestUrl.search || ''
    const targetUrl = `${backendUrl}${targetPath}${queryString}`

    // Get request method and body
    const method = event.method
    const headers: Record<string, string> = {}

    // Copy request headers (excluding problematic ones)
    const reqHeaders = event.headers
    reqHeaders.forEach((value, key) => {
        if (!['host', 'connection', 'transfer-encoding', 'content-length'].includes(key.toLowerCase())) {
            headers[key] = value
        }
    })

    // Prepare fetch options
    const fetchOptions: RequestInit = {
        method,
        headers,
    }

    // Add body for non-GET requests
    if (method !== 'GET' && method !== 'HEAD') {
        const body = await readRawBody(event)
        if (body) {
            fetchOptions.body = body
            // Preserve content-type for form data
            const contentType = event.headers.get('content-type')
            if (contentType) {
                headers['content-type'] = contentType
            }
        }
    }

    try {
        // Fetch from backend
        const response = await fetch(targetUrl, fetchOptions)

        // Get response body as text/json
        const responseData = await response.text()

        // Set response status
        setResponseStatus(event, response.status)

        // Copy response headers (excluding transfer-encoding to prevent duplicate)
        response.headers.forEach((value, key) => {
            if (key.toLowerCase() !== 'transfer-encoding') {
                setHeader(event, key, value)
            }
        })

        // Return response body
        return responseData
    } catch (error) {
        console.error('Proxy error:', error)
        setResponseStatus(event, 502)
        return { error: 'Backend unavailable' }
    }
})
