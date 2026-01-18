/**
 * Composable for handling standardized API responses
 * 
 * Response format:
 * {
 *   success: boolean
 *   code: string
 *   message: string
 *   data: any | any[]
 *   meta: { pagination, sort, filters }
 *   errors: { field, message }[]
 *   timestamp: string
 *   request_id: string
 * }
 */

interface ApiError {
    field: string
    message: string
}

interface Pagination {
    page: number
    limit: number
    total_items: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
}

interface Sort {
    by: string
    order: string
}

interface Meta {
    pagination?: Pagination
    sort?: Sort
    filters?: Record<string, string>
}

interface ApiResponse<T = any> {
    success: boolean
    code: string
    message: string
    data: T
    meta: Meta | null
    errors: ApiError[] | null
    timestamp: string
    request_id: string
}

interface UseApiOptions {
    immediate?: boolean
    watch?: Ref[] | ComputedRef[]
}

export function useApi<T = any>(
    endpoint: string | Ref<string> | ComputedRef<string>,
    options: UseApiOptions = {}
) {
    const data = ref<T | null>(null) as Ref<T | null>
    const meta = ref<Meta | null>(null)
    const loading = ref(false)
    const error = ref<string | null>(null)
    const errors = ref<ApiError[]>([])

    // Pagination state
    const page = ref(1)
    const limit = ref(10)
    const pagination = computed(() => meta.value?.pagination)

    // Get auth token from cookie
    const authToken = useCookie('auth_token')

    async function fetch(params?: Record<string, any>) {
        loading.value = true
        error.value = null
        errors.value = []

        try {
            const url = toValue(endpoint)
            const queryParams = new URLSearchParams()

            // Add pagination params
            queryParams.set('page', page.value.toString())
            queryParams.set('limit', limit.value.toString())

            // Add custom params
            if (params) {
                Object.entries(params).forEach(([key, value]) => {
                    if (value !== undefined && value !== null && value !== '') {
                        queryParams.set(key, value.toString())
                    }
                })
            }

            const fullUrl = `${url}${url.includes('?') ? '&' : '?'}${queryParams.toString()}`

            const response = await $fetch<ApiResponse<T>>(fullUrl, {
                headers: {
                    'Authorization': authToken.value ? `Bearer ${authToken.value}` : '',
                },
            })

            if (response.success) {
                data.value = response.data
                meta.value = response.meta
            } else {
                error.value = response.message
                errors.value = response.errors || []
            }

            return response
        } catch (e: any) {
            console.error('API Error:', e)
            error.value = e.message || 'An error occurred'
            return null
        } finally {
            loading.value = false
        }
    }

    // Pagination helpers
    function setPage(newPage: number) {
        page.value = newPage
        fetch()
    }

    function setLimit(newLimit: number) {
        limit.value = newLimit
        page.value = 1 // Reset to first page
        fetch()
    }

    function refresh() {
        fetch()
    }

    function nextPage() {
        if (pagination.value?.has_next) {
            page.value++
            fetch()
        }
    }

    function prevPage() {
        if (pagination.value?.has_prev) {
            page.value--
            fetch()
        }
    }

    // Auto-fetch on mount if immediate
    if (options.immediate !== false) {
        onMounted(() => fetch())
    }

    // Watch for endpoint changes
    if (options.watch) {
        watch(options.watch, () => {
            page.value = 1
            fetch()
        })
    }

    return {
        // State
        data,
        meta,
        loading,
        error,
        errors,

        // Pagination
        page,
        limit,
        pagination,

        // Methods
        fetch,
        refresh,
        setPage,
        setLimit,
        nextPage,
        prevPage,
    }
}

/**
 * Composable for mutation (POST, PUT, DELETE) with standardized response
 */
export function useApiMutation<T = any, B = any>(
    endpoint: string | Ref<string> | ComputedRef<string>,
    method: 'POST' | 'PUT' | 'DELETE' = 'POST'
) {
    const data = ref<T | null>(null) as Ref<T | null>
    const loading = ref(false)
    const error = ref<string | null>(null)
    const errors = ref<ApiError[]>([])
    const success = ref(false)

    const authToken = useCookie('auth_token')

    async function mutate(body?: B) {
        loading.value = true
        error.value = null
        errors.value = []
        success.value = false

        try {
            const url = toValue(endpoint)

            const response = await $fetch<ApiResponse<T>>(url, {
                method,
                body: body as any,
                headers: {
                    'Authorization': authToken.value ? `Bearer ${authToken.value}` : '',
                    'Content-Type': 'application/json',
                },
            })

            if (response.success) {
                data.value = response.data
                success.value = true
            } else {
                error.value = response.message
                errors.value = response.errors || []
            }

            return response
        } catch (e: any) {
            console.error('API Mutation Error:', e)
            error.value = e.message || 'An error occurred'
            return null
        } finally {
            loading.value = false
        }
    }

    function reset() {
        data.value = null
        error.value = null
        errors.value = []
        success.value = false
    }

    return {
        data,
        loading,
        error,
        errors,
        success,
        mutate,
        reset,
    }
}
