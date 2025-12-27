<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold">Shipments</h2>
        <p class="text-gray-500">Track deliveries and carrier integration</p>
      </div>
      <div class="flex gap-2">
        <UDropdown :items="exportOptions" :popper="{ placement: 'bottom-end' }">
          <UButton icon="i-heroicons-arrow-down-tray" variant="outline" size="sm">Export</UButton>
        </UDropdown>
        <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchData">Refresh</UButton>
        <UButton icon="i-heroicons-plus" @click="openCreate">New Shipment</UButton>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold">{{ shipments.length }}</p>
          <p class="text-sm text-gray-500">Total Shipments</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ pendingShipments }}</p>
          <p class="text-sm text-gray-500">Pending</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-blue-600">{{ inTransitShipments }}</p>
          <p class="text-sm text-gray-500">In Transit</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-green-600">{{ deliveredToday }}</p>
          <p class="text-sm text-gray-500">Delivered Today</p>
        </div>
      </UCard>
      <UCard :ui="{ body: { padding: 'p-4' } }">
        <div class="text-center">
          <p class="text-2xl font-bold text-red-600">{{ issuesCount }}</p>
          <p class="text-sm text-gray-500">Issues</p>
        </div>
      </UCard>
    </div>

    <UCard>
      <DataTable 
        :columns="columns" 
        :rows="shipments" 
        :loading="loading"
        searchable
        :search-keys="['shipment_number', 'tracking_number', 'carrier']"
        empty-message="No shipments yet. Create one to dispatch goods."
      >
        <template #shipment_number-data="{ row }">
          <span class="font-mono font-medium text-blue-600">{{ row.shipment_number }}</span>
        </template>
        <template #carrier-data="{ row }">
          <div class="flex items-center gap-2">
            <UIcon :name="getCarrierIcon(row.carrier)" class="text-gray-400" />
            {{ row.carrier || 'Not assigned' }}
          </div>
        </template>
        <template #tracking_number-data="{ row }">
          <a v-if="row.tracking_number" :href="getTrackingUrl(row)" target="_blank" class="text-blue-600 hover:underline">
            {{ row.tracking_number }}
            <UIcon name="i-heroicons-arrow-top-right-on-square" class="w-3 h-3 inline" />
          </a>
          <span v-else class="text-gray-400">-</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1">
            <UButton icon="i-heroicons-eye" size="xs" color="gray" variant="ghost" @click="viewDetails(row)" />
            <UButton v-if="row.status === 'Pending'" icon="i-heroicons-truck" size="xs" color="blue" variant="ghost" @click="dispatchShipment(row)" title="Dispatch" />
            <UButton v-if="row.status === 'In Transit'" icon="i-heroicons-check" size="xs" color="green" variant="ghost" @click="markDelivered(row)" title="Mark Delivered" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Create Shipment Modal -->
    <FormSlideover 
      v-model="isOpen" 
      title="Create Shipment"
      :loading="submitting"
      @submit="save"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-500 pb-2 border-b">Create a new shipment for delivery orders. Assign carrier and tracking details.</p>
        
        <UFormGroup label="Delivery Order" required hint="Select delivery order to ship" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.do_id" :options="doOptions" placeholder="Select DO..." />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Carrier / Courier" hint="Shipping company" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.courier_id" :options="courierOptions" placeholder="Select courier..." @change="onCourierChange" />
          </UFormGroup>
          <UFormGroup label="Service Type" hint="Speed of delivery" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.service_type" :options="serviceTypeOptions" @change="calcExpectedDelivery" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Tracking Number" hint="Carrier tracking ID" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.tracking_number" placeholder="e.g., JNE-123456789" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Ship Date" hint="Date of dispatch" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.ship_date" type="date" />
          </UFormGroup>
          <UFormGroup label="Expected Delivery" hint="ETA at destination" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.expected_delivery" type="date" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Shipping Cost (Rp)" hint="Total shipping fee" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.shipping_cost" type="number" placeholder="0" />
        </UFormGroup>
        
        <UFormGroup label="Shipping Address" hint="Destination address" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.address" rows="2" placeholder="Full delivery address..." />
        </UFormGroup>
        
        <UFormGroup label="Notes" hint="Special instructions" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.notes" rows="2" placeholder="e.g., Fragile, call before delivery..." />
        </UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const submitting = ref(false)
const isOpen = ref(false)

const shipments = ref<any[]>([])
const deliveryOrders = ref<any[]>([])

const columns = [
  { key: 'shipment_number', label: 'Shipment #', sortable: true },
  { key: 'do_number', label: 'DO #' },
  { key: 'carrier', label: 'Carrier' },
  { key: 'tracking_number', label: 'Tracking' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' }
]

const couriers = ref<any[]>([])

const courierOptions = computed(() => couriers.value.filter(c => c.is_active).map(c => ({ label: c.name, value: c.id })))

const serviceTypeOptions = computed(() => {
  const selected = couriers.value.find(c => c.id === form.courier_id)
  if (selected && selected.service_types) {
    return selected.service_types.split(',').map((s: string) => ({ label: s.trim(), value: s.trim() }))
  }
  return [{ label: 'Regular', value: 'Regular' }, { label: 'Express', value: 'Express' }]
})

const exportOptions = [[
  { label: 'Export as CSV', icon: 'i-heroicons-table-cells', click: () => exportData('csv') },
  { label: 'Export as Excel', icon: 'i-heroicons-document-text', click: () => exportData('xls') },
  { label: 'Export as PDF', icon: 'i-heroicons-document', click: () => exportData('pdf') }
]]

const form = reactive({
  do_id: '',
  courier_id: '',
  service_type: 'Regular',
  tracking_number: '',
  ship_date: new Date().toISOString().split('T')[0],
  expected_delivery: '',
  shipping_cost: 0,
  address: '',
  notes: ''
})

const pendingShipments = computed(() => shipments.value.filter(s => s.status === 'Pending').length)
const inTransitShipments = computed(() => shipments.value.filter(s => s.status === 'In Transit').length)
const deliveredToday = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return shipments.value.filter(s => s.status === 'Delivered' && s.delivered_at?.startsWith(today)).length
})
const issuesCount = computed(() => shipments.value.filter(s => s.status === 'Issue' || s.status === 'Returned').length)

const doOptions = computed(() => deliveryOrders.value.filter(d => d.status === 'Ready').map(d => ({ label: `${d.do_number} - ${d.customer_name || 'Customer'}`, value: d.id })))

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = { Pending: 'yellow', 'In Transit': 'blue', Delivered: 'green', Issue: 'red', Returned: 'orange' }
  return colors[status] || 'gray'
}

const getCarrierIcon = (carrier: string) => {
  if (carrier === 'Own Fleet') return 'i-heroicons-truck'
  if (carrier === 'Pickup') return 'i-heroicons-home'
  return 'i-heroicons-paper-airplane'
}

const getTrackingUrl = (row: any) => {
  const urls: Record<string, string> = {
    'JNE': `https://www.jne.co.id/id/tracking/${row.tracking_number}`,
    'J&T': `https://jet.co.id/track/${row.tracking_number}`,
    'SiCepat': `https://www.sicepat.com/checkAwb/${row.tracking_number}`
  }
  return urls[row.carrier] || '#'
}

const fetchData = async () => {
  loading.value = true
  try {
    const [shipRes, doRes, courierRes] = await Promise.all([
      $api.get('/logistics/shipments').catch(() => ({ data: [] })),
      $api.get('/delivery/orders').catch(() => ({ data: [] })),
      $api.get('/logistics/couriers').catch(() => ({ data: [] }))
    ])
    shipments.value = shipRes.data || []
    deliveryOrders.value = doRes.data || []
    couriers.value = courierRes.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const onCourierChange = () => {
  const selected = couriers.value.find(c => c.id === form.courier_id)
  if (selected) {
    form.service_type = selected.default_service || 'Regular'
    form.shipping_cost = selected.base_cost || 0
    calcExpectedDelivery()
  }
}

const calcExpectedDelivery = () => {
  const selected = couriers.value.find(c => c.id === form.courier_id)
  if (selected && form.ship_date) {
    const isExpress = form.service_type?.toLowerCase().includes('express') || form.service_type?.toLowerCase().includes('same day')
    const days = isExpress ? (selected.express_lead_days || 1) : (selected.standard_lead_days || 3)
    const shipDate = new Date(form.ship_date)
    shipDate.setDate(shipDate.getDate() + days)
    form.expected_delivery = shipDate.toISOString().split('T')[0]
  }
}

const openCreate = () => {
  Object.assign(form, { do_id: '', courier_id: '', service_type: 'Regular', tracking_number: '', ship_date: new Date().toISOString().split('T')[0], expected_delivery: '', shipping_cost: 0, address: '', notes: '' })
  isOpen.value = true
}

const viewDetails = (row: any) => {
  toast.add({ title: row.shipment_number, description: `Carrier: ${row.carrier} | Tracking: ${row.tracking_number || 'N/A'}`, color: 'blue' })
}

const save = async () => {
  if (!form.do_id) {
    toast.add({ title: 'Validation Error', description: 'Please select a delivery order', color: 'red' })
    return
  }
  submitting.value = true
  try {
    await $api.post('/logistics/shipments', form)
    toast.add({ title: 'Created', description: 'Shipment created successfully', color: 'green' })
    isOpen.value = false
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const dispatchShipment = async (row: any) => {
  try {
    await $api.put(`/logistics/shipments/${row.id}/dispatch`)
    toast.add({ title: 'Dispatched', description: 'Shipment is now in transit', color: 'blue' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const markDelivered = async (row: any) => {
  try {
    await $api.put(`/logistics/shipments/${row.id}/deliver`)
    toast.add({ title: 'Delivered', description: 'Shipment marked as delivered', color: 'green' })
    fetchData()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed', color: 'red' })
  }
}

const exportData = (format: string) => {
  const data = shipments.value.map((s: any) => ({
    'Shipment #': s.shipment_number,
    'DO #': s.do_number || '',
    'Carrier': s.carrier || '',
    'Tracking': s.tracking_number || '',
    'Service': s.service_type || '',
    'Status': s.status
  }))
  
  if (format === 'csv' || format === 'xls') {
    const headers = Object.keys(data[0] || {})
    const separator = format === 'csv' ? ',' : '\t'
    const content = [headers.join(separator), ...data.map((row: any) => headers.map(h => `"${row[h] || ''}"`).join(separator))].join('\n')
    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'application/vnd.ms-excel' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `shipments.${format === 'csv' ? 'csv' : 'xls'}`; a.click()
    toast.add({ title: 'Exported', description: `Shipments exported as ${format.toUpperCase()}`, color: 'green' })
  } else if (format === 'pdf') {
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html><head><title>Shipments</title>
        <style>body{font-family:Arial;} table{width:100%;border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;text-align:left;} th{background:#f4f4f4;}</style>
        </head><body>
        <h1>Shipments Report</h1>
        <p>Exported: ${new Date().toLocaleDateString()}</p>
        <table><tr>${Object.keys(data[0] || {}).map(h => `<th>${h}</th>`).join('')}</tr>
        ${data.map((row: any) => `<tr>${Object.values(row).map(v => `<td>${v}</td>`).join('')}</tr>`).join('')}
        </table></body></html>
      `)
      printWindow.document.close()
      printWindow.print()
    }
  }
}

onMounted(() => { fetchData() })
</script>
