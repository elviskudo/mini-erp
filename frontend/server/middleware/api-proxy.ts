// Server middleware to proxy /api requests to API Gateway
// This fixes the duplicate Transfer-Encoding header issue with nitro proxy

export default defineEventHandler(async (event) => {
    const requestUrl = getRequestURL(event)
    const path = requestUrl.pathname

    // Only handle /api routes, but EXCLUDE internal Nuxt paths like /_nuxt_icon
    if (!path.startsWith('/api/') || path.startsWith('/api/_nuxt')) {
        return
    }

    // Use API Gateway instead of legacy backend
    const backendUrl = 'http://api-gateway:8000'
    // Transform /api/xxx to /api/v1/xxx for gateway routing
    const targetPath = path.replace('/api/', '/api/v1/')
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

    // Extract auth_token from cookie and set Authorization header if not already present
    if (!headers['authorization']) {
        const cookieHeader = event.headers.get('cookie') || ''
        const authTokenMatch = cookieHeader.match(/auth_token=([^;]+)/)
        if (authTokenMatch) {
            headers['authorization'] = `Bearer ${authTokenMatch[1]}`
        }
    }

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

        // Get response body as text
        const responseText = await response.text()

        // Set response status
        setResponseStatus(event, response.status)

        // Copy response headers (excluding transfer-encoding to prevent duplicate)
        response.headers.forEach((value, key) => {
            if (key.toLowerCase() !== 'transfer-encoding') {
                setHeader(event, key, value)
            }
        })

        // IMPORTANT: Return raw text directly to prevent Nuxt from re-serializing
        // Set content-type explicitly to ensure proper handling
        const contentType = response.headers.get('content-type') || 'application/json'
        setHeader(event, 'content-type', contentType)

        // Return raw response text (don't parse JSON - let browser handle it)
        return responseText
    } catch (error) {
        console.error('Proxy error:', error)
        setResponseStatus(event, 502)
        setHeader(event, 'content-type', 'application/json')
        return JSON.stringify({ error: 'Backend unavailable' })
    }
})
