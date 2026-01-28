<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Purchase Requests</h2>
        <p class="text-gray-500">Manage purchase requisitions</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportItems">
          <UButton color="gray" variant="outline" icon="i-heroicons-arrow-down-tray">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-cog-6-tooth" variant="soft" color="gray" to="/settings/approval-rules">Approval Rules</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreateModal">Create Request</UButton>
      </div>
    </div>

    <!-- DataTable with search, sort, pagination -->
    <UCard :ui="{ body: { padding: '' } }">
      <template #header>
        <div class="flex items-center justify-between gap-3 px-4">
          <UInput v-model="search" icon="i-heroicons-magnifying-glass" placeholder="Search PR..." class="w-64" />
          <div class="flex gap-2 items-center text-sm text-gray-500">
            Total: {{ filteredPrs.length }} PR
          </div>
        </div>
      </template>
      <UTable 
        :columns="columns" 
        :rows="paginatedPrs" 
        :loading="loading"
        :sort="{ column: 'created_at', direction: 'desc' }"
        @update:sort="onSort"
      >
         <template #pr_number-data="{ row }">
            <span class="font-mono text-sm font-medium">{{ row.pr_number }}</span>
        </template>
         <template #status-data="{ row }">
            <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
         <template #actions-data="{ row }">
             <div class="flex gap-2">
                 <UButton size="xs" color="gray" variant="ghost" icon="i-heroicons-eye" @click="openDetailModal(row)">View</UButton>
                 <UButton v-if="row.status === 'Draft'" size="xs" color="green" variant="soft" @click="openApproveModal(row.id)">Approve</UButton>
                 <UButton v-if="row.status === 'Draft'" size="xs" color="red" variant="soft" @click="openRejectModal(row.id)">Reject</UButton>
                 <UButton v-if="row.status === 'Approved'" size="xs" color="blue" variant="soft" @click="openConvertModal(row)">Convert to PO</UButton>
             </div>
        </template>
      </UTable>
      <template #footer>
        <div class="flex items-center justify-between px-4">
          <USelect v-model="pageSize" :options="[5, 10, 20, 50]" class="w-20" />
          <UPagination v-model="currentPage" :page-count="pageSize" :total="filteredPrs.length" />
        </div>
      </template>
    </UCard>

    <!-- Approve Confirmation Modal (SweetAlert style) -->
    <UModal v-model="isApproveOpen">
      <div class="p-6 text-center space-y-4">
        <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100">
          <span class="i-heroicons-check-circle text-4xl text-green-600"></span>
        </div>
        <h3 class="text-xl font-semibold text-gray-900">Approve Purchase Request?</h3>
        <p class="text-gray-600">PR ini akan di-approve dan siap untuk dikonversi ke PO.</p>
        <div class="flex justify-center gap-3 pt-2">
          <UButton variant="ghost" @click="isApproveOpen = false">Cancel</UButton>
          <UButton color="green" :loading="submitting" @click="doApprove">Ya, Approve</UButton>
        </div>
      </div>
    </UModal>

    <!-- Create PR Slideover - 1/3 page width -->
    <FormSlideover
      v-model="isCreateOpen"
      title="New Purchase Request"
      submit-label="Submit Request"
      :loading="submitting"
      :disabled="!isFormValid"
      @submit="createPr"
    >
      <div class="space-y-4">
        <!-- Header Fields -->
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Priority" required hint="Urgency level" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.priority" :options="priorityOptions" />
          </UFormGroup>
          <UFormGroup label="Required Date" required hint="When items are needed" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.required_date" type="date" />
          </UFormGroup>
        </div>

        <UFormGroup label="Notes" hint="Additional instructions or justification" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="3" placeholder="e.g. For project Alpha..." />
        </UFormGroup>

        <!-- Items Section -->
        <div class="border-t pt-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <h4 class="text-sm font-medium text-gray-900">Request Items</h4>
              <p class="text-xs text-gray-500">List products to purchase</p>
            </div>
            <UButton size="xs" icon="i-heroicons-plus" variant="soft" @click="addItem">Add Item</UButton>
          </div>

          <div class="space-y-3">
            <div v-for="(item, index) in form.items" :key="index" class="p-3 bg-gray-50 rounded-lg space-y-3 border border-gray-100">
              <div class="flex gap-3 items-start">
                <UFormGroup label="Product" class="flex-1" required :ui="{ label: 'text-xs mb-1' }">
                  <USelectMenu 
                    v-model="item.product_id" 
                    :options="products" 
                    option-attribute="name" 
                    value-attribute="id" 
                    placeholder="Search Product..."
                    searchable
                    @change="onProductChange(index)"
                  >
                    <template #option="{ option }">
                        <div class="flex flex-col">
                            <span class="font-medium">{{ option.name }}</span>
                            <span class="text-xs text-gray-400">{{ option.code }}</span>
                        </div>
                    </template>
                  </USelectMenu>
                </UFormGroup>
                <UFormGroup label="Qty" class="w-24" required :ui="{ label: 'text-xs mb-1' }">
                  <UInput 
                    v-model="item.quantity" 
                    type="number" 
                    min="1" 
                    :max="item.max_stock || 99999"
                    @blur="onQtyBlur(index)"
                  />
                </UFormGroup>
                <UButton 
                  icon="i-heroicons-trash" 
                  color="red" 
                  variant="ghost" 
                  class="mt-6"
                  size="xs"
                  :disabled="form.items.length === 1"
                  @click="removeItem(index)" 
                />
              </div>
              
              <!-- Stock Info Display -->
              <div v-if="item.stock_info" class="text-xs bg-white p-2 rounded border border-gray-100">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-gray-500">Available Stock:</span>
                  <span class="font-medium text-green-600">{{ item.stock_info.available_stock }} {{ item.product?.uom || 'Units' }}</span>
                </div>
                <div v-if="item.stock_info.warehouses?.length" class="space-y-1">
                  <div v-for="(wh, idx) in item.stock_info.warehouses" :key="idx" class="flex justify-between text-gray-400">
                    <span>{{ wh.warehouse_name }}</span>
                    <span>{{ wh.quantity }}</span>
                  </div>
                </div>
              </div>

              <!-- Stock Error Display -->
              <div v-if="item.stock_error" class="text-xs text-red-600 flex items-center gap-1">
                <UIcon name="i-heroicons-exclamation-triangle" class="w-3 h-3" />
                {{ item.stock_error }}
              </div>
            </div>
          </div>
          
          <div v-if="form.items.length === 0" class="text-center py-8 text-gray-400 bg-gray-50 rounded-lg border border-dashed">
            No items added. Click "Add Item" to start.
          </div>
        </div>
      </div>
    </FormSlideover>

    <!-- Convert to PO Slideover -->
    <FormSlideover
      v-model="isConvertOpen"
      title="Convert PR to PO"
      submit-label="Generate PO"
      :loading="submitting"
      :disabled="!convertForm.vendor_id"
      @submit="convertToPo"
    >
      <div class="space-y-4">
        <UFormGroup label="Select Vendor" required hint="Choose supplier for this purchase order" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="convertForm.vendor_id" :options="vendors" option-attribute="name" value-attribute="id" placeholder="Search and select vendor..." />
        </UFormGroup>
        
        <div v-if="selectedPr" class="border-t pt-4">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-medium">Set Unit Prices</p>
            <p class="text-xs text-gray-400">Enter price per unit for each item</p>
          </div>
          <div class="space-y-3">
            <div v-for="item in selectedPr.items" :key="item.id" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <div>
                <p class="font-medium">{{ item.product?.name }}</p>
                <p class="text-sm text-gray-500">Qty: {{ item.quantity }}</p>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-gray-500 text-sm">Rp</span>
                <UInput 
                  v-model="convertForm.price_map[item.product_id]" 
                  type="number" 
                  placeholder="0" 
                  class="w-32"
                  :ui="{ icon: { trailing: { pointer: '' } } }"
                />
              </div>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">* Total = Qty × Unit Price for each item</p>
        </div>
      </div>
    </FormSlideover>

    <!-- PR Detail Modal -->
    <UModal v-model="isDetailOpen" :ui="{ width: 'sm:max-w-2xl' }">
      <div class="p-6 space-y-4" v-if="detailPr">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-semibold text-gray-900">{{ detailPr.pr_number }}</h3>
          <UBadge :color="getStatusColor(detailPr.status)" size="lg">{{ detailPr.status }}</UBadge>
        </div>
        
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Dibuat pada</p>
            <p class="font-medium">{{ new Date(detailPr.created_at).toLocaleDateString('id-ID') }}</p>
          </div>
          <div>
            <p class="text-gray-500">Tanggal Dibutuhkan</p>
            <p class="font-medium">{{ detailPr.required_date ? new Date(detailPr.required_date).toLocaleDateString('id-ID') : '-' }}</p>
          </div>
        </div>

        <div class="border-t pt-4">
          <h4 class="font-medium mb-3">Items</h4>
          <UTable :columns="[{key: 'product', label: 'Product'}, {key: 'quantity', label: 'Qty'}]" :rows="detailPr.items?.map((i: any) => ({product: i.product?.name || 'Unknown', quantity: i.quantity})) || []" />
        </div>

        <div v-if="detailPr.notes" class="border-t pt-4">
          <h4 class="font-medium mb-2">Notes</h4>
          <p class="text-gray-600">{{ detailPr.notes }}</p>
        </div>

        <div v-if="detailPr.status === 'Rejected'" class="border-t pt-4 bg-red-50 p-4 rounded-lg">
          <h4 class="font-medium text-red-800 mb-2">Rejection Info</h4>
          <p class="text-red-700">{{ detailPr.reject_reason }}</p>
          <p class="text-sm text-red-600 mt-1">Ditolak pada: {{ detailPr.rejected_at ? new Date(detailPr.rejected_at).toLocaleDateString('id-ID') : '-' }}</p>
        </div>

        <div class="flex justify-end pt-2">
          <UButton variant="ghost" @click="isDetailOpen = false">Close</UButton>
        </div>
      </div>
    </UModal>

    <!-- Reject Modal -->
    <UModal v-model="isRejectOpen">
      <div class="p-6 space-y-4">
        <div class="flex items-center gap-3 text-red-600">
          <span class="i-heroicons-exclamation-triangle text-2xl"></span>
          <h3 class="text-lg font-semibold">Reject Purchase Request</h3>
        </div>
        <p class="text-gray-600">Berikan alasan mengapa PR ini ditolak:</p>
        <UFormGroup label="Reason" required>
          <UTextarea v-model="rejectReason" placeholder="Masukkan alasan reject..." rows="3" />
        </UFormGroup>
        <div class="flex justify-end gap-3">
          <UButton variant="ghost" @click="isRejectOpen = false">Cancel</UButton>
          <UButton color="red" :loading="submitting" @click="rejectPr">Reject</UButton>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const { $api } = useNuxtApp()
const toast = useToast()
const isCreateOpen = ref(false)
const isConvertOpen = ref(false)
const isRejectOpen = ref(false)
const isApproveOpen = ref(false)
const isDetailOpen = ref(false)
const loading = ref(false)
const submitting = ref(false)

// DataTable
const search = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const sortColumn = ref('created_at')
const sortDirection = ref<'asc' | 'desc'>('desc')

const prs = ref<any[]>([])
const products = ref<any[]>([])
const rejectReason = ref('')
const selectedPrId = ref<string | null>(null)
const approvePrId = ref<string | null>(null)
const detailPr = ref<any>(null)
const vendors = ref<any[]>([])

const selectedPr = ref<any>(null)

const columns = [
  { key: 'pr_number', label: 'PR Number', sortable: true },
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'actions', label: '' }
]

// DataTable computed properties
const filteredPrs = computed(() => {
    if (!search.value) return prs.value
    const q = search.value.toLowerCase()
    return prs.value.filter((pr: any) => 
        pr.pr_number?.toLowerCase().includes(q) ||
        pr.status?.toLowerCase().includes(q)
    )
})

const paginatedPrs = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredPrs.value.slice(start, end)
})

const onSort = (sort: { column: string, direction: 'asc' | 'desc' }) => {
    sortColumn.value = sort.column
    sortDirection.value = sort.direction
}

// Form validation - submit only enabled when all items are valid
const isFormValid = computed(() => {
    // Must have at least one item
    if (form.items.length === 0) return false
    
    // All items must have product_id, quantity > 0, and no stock_error
    return form.items.every((item: any) => 
        item.product_id && 
        item.quantity > 0 && 
        !item.stock_error
    )
})

const form = reactive({
    priority: 'Normal',
    required_date: new Date().toISOString().split('T')[0],
    notes: '',
    items: [] as any[]
})

const priorityOptions = ['Low', 'Normal', 'High']

const convertForm = reactive({
    vendor_id: '',
    price_map: {} as Record<string, number>
})

const getStatusColor = (status: string) => {
    switch(status) {
        case 'Draft': return 'gray'
        case 'Approved': return 'blue'
        case 'Converted': return 'green'
        case 'Rejected': return 'red'
        default: return 'primary'
    }
}

// Export functionality
const exportItems = [[
    {
        label: 'Export as Excel',
        icon: 'i-heroicons-table-cells',
        click: () => exportData('xlsx')
    },
    {
        label: 'Export as CSV',
        icon: 'i-heroicons-document-text',
        click: () => exportData('csv')
    },
    {
        label: 'Export as PDF',
        icon: 'i-heroicons-document',
        click: () => exportData('pdf')
    }
]]

const exportData = async (format: string) => {
    const data = filteredPrs.value.map((pr: any) => ({
        'PR Number': pr.pr_number,
        'Status': pr.status,
        'Created At': pr.created_at ? new Date(pr.created_at).toLocaleDateString('id-ID') : '-',
        'Items': pr.items?.length || 0
    }))
    
    if (format === 'csv') {
        const headers = Object.keys(data[0] || {}).join(',')
        const rows = data.map((row: any) => Object.values(row).join(',')).join('\n')
        const csv = headers + '\n' + rows
        downloadFile(csv, 'purchase_requests.csv', 'text/csv')
    } else if (format === 'xlsx') {
        // Simple Excel export using CSV with xls extension
        const headers = Object.keys(data[0] || {}).join('\t')
        const rows = data.map((row: any) => Object.values(row).join('\t')).join('\n')
        const xls = headers + '\n' + rows
        downloadFile(xls, 'purchase_requests.xls', 'application/vnd.ms-excel')
    } else if (format === 'pdf') {
        // Generate simple HTML table and print as PDF with company header
        const companyName = authStore.user?.tenant_name || 'PT. Mini ERP Indonesia'
        const exportDate = new Date().toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' })
        const html = `
            <html><head><title>Purchase Requests</title>
            <style>
                body{font-family:Arial,sans-serif;margin:20px}
                .header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #2563eb;padding-bottom:15px;margin-bottom:20px}
                .company-name{font-size:20px;font-weight:bold;color:#1e40af}
                .report-info{text-align:right;color:#666}
                table{border-collapse:collapse;width:100%}
                th,td{border:1px solid #ddd;padding:10px;text-align:left}
                th{background:#2563eb;color:white}
                .footer{margin-top:20px;text-align:center;color:#666;font-size:12px}
            </style></head>
            <body>
                <div class="header">
                    <div>
                        <div class="company-name">${companyName}</div>
                        <div style="color:#666">Jakarta, Indonesia</div>
                    </div>
                    <div class="report-info">
                        <div style="font-size:18px;font-weight:bold;color:#2563eb">PURCHASE REQUESTS</div>
                        <div>Export Date: ${exportDate}</div>
                    </div>
                </div>
                <table>
                    <tr>${Object.keys(data[0] || {}).map(k => '<th>' + k + '</th>').join('')}</tr>
                    ${data.map((row: any) => '<tr>' + Object.values(row).map(v => '<td>' + v + '</td>').join('') + '</tr>').join('')}
                </table>
                <div class="footer">Generated by Mini-ERP System on ${exportDate}</div>
            </body></html>
        `
        const win = window.open('', '_blank')
        if (win) {
            win.document.write(html)
            win.document.close()
            win.print()
        }
    }
    toast.add({ title: 'Export Started', description: `Exporting as ${format.toUpperCase()}` })
}

const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
}

const fetchData = async () => {
    loading.value = true
    try {
        const [prRes, prodRes, vendRes]: any = await Promise.all([
            $api.get('/procurement/purchase-requests'),
            $api.get('/manufacturing/products'),
            $api.get('/procurement/vendors')
        ])
        prs.value = prRes.data.data || prRes 
        products.value = prodRes.data.data || prodRes
        vendors.value = vendRes.data.data || vendRes
    } catch (e) { console.error(e) } 
    finally { loading.value = false }
}

const openCreateModal = () => {
    form.items = [{ product_id: '', quantity: 1, stock_info: null, stock_error: null, max_stock: 0 }]
    isCreateOpen.value = true
}

const openDetailModal = (pr: any) => {
    detailPr.value = pr
    isDetailOpen.value = true
}

const openApproveModal = (id: string) => {
    approvePrId.value = id
    isApproveOpen.value = true
}

const openRejectModal = (id: string) => {
    selectedPrId.value = id
    rejectReason.value = ''
    isRejectOpen.value = true
}

const openConvertModal = (pr: any) => {
    selectedPr.value = pr
    convertForm.vendor_id = ''
    convertForm.price_map = {}
    
    // Initialize price map from items
    pr.items?.forEach((item: any) => {
        if (item.product_id) {
            convertForm.price_map[item.product_id] = 0 // Default price could be fetched from product cost
        }
    })
    
    isConvertOpen.value = true
}

const addItem = () => form.items.push({ product_id: '', quantity: 1, stock_info: null, stock_error: null, max_stock: 0 })
const removeItem = (idx: number) => form.items.splice(idx, 1)

const onProductChange = async (index: number) => {
    const item = form.items[index]
    if (!item.product_id) {
        item.stock_info = null
        item.stock_error = null
        item.max_stock = 0
        return
    }
    
    try {
        // Fetch stock batches from inventory service
        const stockBatches: any[] = await $api.get(`/inventory/stock?product_id=${item.product_id}`)
        
        // Calculate total available stock
        const totalStock = stockBatches.reduce((sum: number, batch: any) => sum + (batch.quantity || 0), 0)
        
        item.stock_info = {
            available_stock: totalStock,
            warehouses: stockBatches.map(b => ({ warehouse_name: b.warehouse_id, location_code: 'N/A', quantity: b.quantity })) // Simplified mapping
        }

        item.max_stock = totalStock
        item.stock_error = null
        
        // Auto-set qty to available stock if it's less than current qty
        if (item.quantity > totalStock) {
            item.quantity = totalStock
        }
    } catch (e) {
        item.stock_info = null
        item.stock_error = 'Gagal mengambil data stok'
    }
}

const onQtyBlur = async (index: number) => {
    const item = form.items[index]
    if (!item.product_id || !item.quantity) return
    
    try {
        const stockBatches: any[] = await $api.get(`/inventory/stock?product_id=${item.product_id}`)
        
        // Calculate total available stock
        const available_stock = stockBatches.reduce((sum: number, batch: any) => sum + (batch.quantity || 0), 0)
        
        if (item.quantity > available_stock) {
            item.stock_error = `Qty (${item.quantity}) melebihi stok tersedia (${available_stock})`
        } else {
            item.stock_error = null
        }
    } catch (e) {
        item.stock_error = 'Gagal validasi stok'
    }
}

const createPr = async () => {
    submitting.value = true
    try {
        await $api.post('/procurement/purchase-requests', form)
        toast.add({ title: 'Success', description: 'Purchase request created.' })
        isCreateOpen.value = false
        fetchData()
    } catch (e) { 
        toast.add({ title: 'Error', description: 'Failed to create request.', color: 'red' })
    }
    finally { submitting.value = false }
}

const doApprove = async () => {
    if (!approvePrId.value) return
    submitting.value = true
    try {
        await $api.post(`/procurement/purchase-requests/${approvePrId.value}/approve`, {})
        toast.add({ 
            title: '✅ Approved!', 
            description: 'Purchase Request berhasil di-approve.',
            color: 'green'
        })
        isApproveOpen.value = false
        fetchData()
    } catch (e: any) { 
        toast.add({ title: 'Error', description: e.response?._data?.message || 'Failed to approve.', color: 'red' })
    } finally {
        submitting.value = false
    }
}

// ... (skip detail modal)

const rejectPr = async () => {
    if (!rejectReason.value.trim()) {
        toast.add({ title: 'Error', description: 'Alasan reject harus diisi!', color: 'red' })
        return
    }
    
    submitting.value = true
    try {
        await $api.post(`/procurement/purchase-requests/${selectedPrId.value}/reject`, { reason: rejectReason.value })
        toast.add({ 
            title: '❌ Rejected', 
            description: 'Purchase Request berhasil di-reject.',
            color: 'red'
        })
        isRejectOpen.value = false
        fetchData()
    } catch (e) { 
        toast.add({ title: 'Error', description: 'Failed to reject.', color: 'red' })
    } finally {
        submitting.value = false
    }
}

const convertToPo = async () => {
    if (!selectedPr.value) return
    submitting.value = true
    try {
        const payload = {
            pr_id: selectedPr.value.id,
            vendor_id: convertForm.vendor_id,
            price_map: convertForm.price_map
        }
        await $api.post('/procurement/purchase-orders/from-pr', payload)
        toast.add({ title: 'Success', description: 'PO Created!' })
        isConvertOpen.value = false
        fetchData()
        navigateTo('/procurement/orders')
    } catch (e) { 
        toast.add({ title: 'Error', description: 'Failed to convert.', color: 'red' })
    }
    finally { submitting.value = false }
}

onMounted(() => {
    fetchData()
})
</script>
