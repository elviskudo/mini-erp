<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Email & Broadcast</h1>
        <p class="text-gray-500">Send marketing emails and broadcasts to customers</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Broadcast</UButton>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4">
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ stats.sent }}</div>
          <div class="text-sm text-gray-500">Emails Sent</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ stats.delivered }}</div>
          <div class="text-sm text-gray-500">Delivered</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-purple-600">{{ stats.opened }}</div>
          <div class="text-sm text-gray-500">Opened</div>
        </div>
      </UCard>
      <UCard>
        <div class="text-center">
          <div class="text-2xl font-bold text-orange-600">{{ stats.clicked }}</div>
          <div class="text-sm text-gray-500">Clicked</div>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="broadcasts" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #recipients-data="{ row }">
          <span class="text-gray-600">{{ row.recipients_count || 0 }} recipients</span>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="getStatusColor(row.status)" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #sent_at-data="{ row }">
          <span class="text-sm text-gray-500">{{ row.sent_at ? formatDate(row.sent_at) : '-' }}</span>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton v-if="row.status === 'draft'" icon="i-heroicons-paper-airplane" color="primary" variant="ghost" size="xs" @click="sendBroadcast(row)" />
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" :disabled="row.status === 'sent'" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="confirmDelete(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Broadcast' : 'New Broadcast'" :loading="saving" @submit="save" size="lg">
      <div class="space-y-4">
        <UFormGroup label="Subject" required>
          <UInput v-model="form.subject" placeholder="🎉 Special Offer Just for You!" />
        </UFormGroup>
        <UFormGroup label="From Name">
          <UInput v-model="form.from_name" placeholder="Your Company" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Link to Campaign">
            <USelectMenu v-model="form.campaign_id" :options="campaignOptions" value-attribute="value" option-attribute="label" searchable placeholder="None" />
          </UFormGroup>
          <UFormGroup label="Recipient List">
            <USelectMenu v-model="form.recipient_type" :options="['All Customers', 'All Leads', 'Specific Segment', 'Manual List']" />
          </UFormGroup>
        </div>
        <UFormGroup v-if="form.recipient_type === 'Manual List'" label="Email Addresses (one per line)">
          <UTextarea v-model="form.manual_emails" rows="4" placeholder="john@example.com&#10;jane@example.com" />
        </UFormGroup>
        <UFormGroup label="Email Content (HTML)" required>
          <UTextarea v-model="form.content" rows="12" class="font-mono text-sm" placeholder="<html>...</html>" />
        </UFormGroup>
        <UFormGroup label="Preview Text">
          <UInput v-model="form.preview_text" placeholder="First line preview in inbox" />
        </UFormGroup>
        <div class="border-t pt-4">
          <UFormGroup label="Schedule">
            <div class="flex items-center gap-4">
              <URadio v-model="form.schedule_type" value="now" label="Send Now" />
              <URadio v-model="form.schedule_type" value="scheduled" label="Schedule for Later" />
            </div>
          </UFormGroup>
          <UFormGroup v-if="form.schedule_type === 'scheduled'" label="Send At" class="mt-3">
            <UInput v-model="form.scheduled_at" type="datetime-local" />
          </UFormGroup>
        </div>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const editMode = ref(false)

const broadcasts = ref([])
const campaigns = ref<any[]>([])
const pagination = ref(null)
const currentPage = ref(1)

const stats = computed(() => ({
    sent: broadcasts.value.reduce((s: number, b: any) => s + (b.recipients_count || 0), 0),
    delivered: Math.floor(broadcasts.value.reduce((s: number, b: any) => s + (b.recipients_count || 0), 0) * 0.95),
    opened: Math.floor(broadcasts.value.reduce((s: number, b: any) => s + (b.recipients_count || 0), 0) * 0.35),
    clicked: Math.floor(broadcasts.value.reduce((s: number, b: any) => s + (b.recipients_count || 0), 0) * 0.12)
}))

const columns = [
    { key: 'subject', label: 'Subject', sortable: true },
    { key: 'recipients', label: 'Recipients' },
    { key: 'status', label: 'Status' },
    { key: 'sent_at', label: 'Sent At' },
    { key: 'actions', label: '' }
]

const campaignOptions = computed(() => [{ label: 'None', value: '' }, ...campaigns.value.map(c => ({ label: c.name, value: c.id }))])
const formatDate = (d: string) => d ? new Date(d).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) : '-'
const getStatusColor = (s: string) => ({ draft: 'gray', scheduled: 'blue', sending: 'yellow', sent: 'green', failed: 'red' }[s] || 'gray')

const form = reactive({
    id: '', subject: '', from_name: '', campaign_id: '', recipient_type: 'All Customers',
    manual_emails: '', content: '', preview_text: '', schedule_type: 'now', scheduled_at: ''
})

const fetchData = async () => {
    loading.value = true
    try {
        // Mock data
        broadcasts.value = [
            { id: '1', subject: '🎉 Year End Sale!', recipients_count: 500, status: 'sent', sent_at: '2026-01-15T10:00:00Z' },
            { id: '2', subject: 'New Product Launch', recipients_count: 350, status: 'scheduled', scheduled_at: '2026-01-25T09:00:00Z' },
            { id: '3', subject: 'Welcome Email Template', recipients_count: 0, status: 'draft' }
        ]
        pagination.value = { page: 1, limit: 10, total_items: 3, total_pages: 1 }
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
    loadCampaigns()
}

const loadCampaigns = async () => {
    try { campaigns.value = (await $api.get('/crm/campaigns', { params: { limit: 100 } })).data?.data || [] } catch(e) {}
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const openCreate = () => { resetForm(); editMode.value = false; isOpen.value = true }
const openEdit = (row: any) => { resetForm(); editMode.value = true; Object.assign(form, row); isOpen.value = true }
const resetForm = () => { Object.assign(form, { id: '', subject: '', from_name: '', campaign_id: '', recipient_type: 'All Customers', manual_emails: '', content: '', preview_text: '', schedule_type: 'now', scheduled_at: '' }) }

const save = async () => {
    if (!form.subject || !form.content) return toast.add({ title: 'Error', description: 'Subject and content required', color: 'red' })
    saving.value = true
    try {
        toast.add({ title: 'Saved', description: 'Broadcast saved (mock)' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const sendBroadcast = async (row: any) => {
    if (!confirm(`Send broadcast "${row.subject}" to all recipients?`)) return
    toast.add({ title: 'Sending', description: 'Broadcast is being sent (mock)' })
    fetchData()
}

const confirmDelete = async (row: any) => {
    if (!confirm(`Delete broadcast "${row.subject}"?`)) return
    toast.add({ title: 'Deleted', description: 'Broadcast deleted (mock)' })
    fetchData()
}

onMounted(() => fetchData())
</script>
