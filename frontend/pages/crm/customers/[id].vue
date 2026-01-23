<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4 mb-6">
      <UButton icon="i-heroicons-arrow-left" color="gray" variant="ghost" @click="$router.back()" />
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ customer?.name || 'Customer Details' }}</h1>
        <p class="text-gray-500">{{ customer?.email }}</p>
      </div>
      <div class="flex-1" />
      <UButton icon="i-heroicons-pencil" variant="outline" @click="editCustomer">Edit</UButton>
    </div>

    <!-- Customer Info Card -->
    <UCard>
      <div class="grid grid-cols-4 gap-6 text-sm">
        <div><span class="text-gray-500">Phone:</span><br />{{ customer?.phone || '-' }}</div>
        <div><span class="text-gray-500">Type:</span><br />{{ customer?.type || 'Individual' }}</div>
        <div><span class="text-gray-500">Credit Limit:</span><br />{{ formatCurrency(customer?.credit_limit) }}</div>
        <div><span class="text-gray-500">Outstanding:</span><br />{{ formatCurrency(customer?.outstanding_balance) }}</div>
      </div>
    </UCard>

    <!-- Activity Tabs -->
    <UTabs v-model="activeTab" :items="tabs">
      <template #item="{ item }">
        <UCard class="mt-4">
          <!-- Emails Tab -->
          <div v-if="item.key === 'emails'" class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold">Email Communications</h3>
              <UButton size="sm" icon="i-heroicons-plus" @click="showEmailForm = true">Compose</UButton>
            </div>
            <div v-if="emails.length === 0" class="text-center text-gray-500 py-8">No emails yet</div>
            <div v-for="email in emails" :key="email.id" class="border rounded-lg p-4">
              <div class="flex justify-between items-start mb-2">
                <div>
                  <UBadge :color="email.direction === 'outgoing' ? 'blue' : 'green'" size="xs" class="mr-2">{{ email.direction }}</UBadge>
                  <span class="font-medium">{{ email.subject }}</span>
                </div>
                <span class="text-xs text-gray-500">{{ formatDate(email.sent_at) }}</span>
              </div>
              <p class="text-sm text-gray-600 line-clamp-2">{{ email.body }}</p>
            </div>
          </div>

          <!-- Calls Tab -->
          <div v-if="item.key === 'calls'" class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold">Call Logs</h3>
              <UButton size="sm" icon="i-heroicons-plus" @click="showCallForm = true">Log Call</UButton>
            </div>
            <div v-if="calls.length === 0" class="text-center text-gray-500 py-8">No call logs yet</div>
            <div v-for="call in calls" :key="call.id" class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
              <UIcon :name="call.direction === 'outgoing' ? 'i-heroicons-phone-arrow-up-right' : 'i-heroicons-phone-arrow-down-left'" :class="call.direction === 'outgoing' ? 'text-blue-500' : 'text-green-500'" class="text-xl" />
              <div class="flex-1">
                <div class="font-medium">{{ call.phone_number }}</div>
                <div class="text-xs text-gray-500">{{ call.notes || 'No notes' }}</div>
              </div>
              <div class="text-right">
                <div>{{ formatDuration(call.duration) }}</div>
                <div class="text-xs text-gray-500">{{ formatDate(call.call_time) }}</div>
              </div>
              <UBadge :color="call.status === 'completed' ? 'green' : 'orange'" size="xs">{{ call.status }}</UBadge>
            </div>
          </div>

          <!-- Meetings Tab -->
          <div v-if="item.key === 'meetings'" class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold">Meetings</h3>
              <UButton size="sm" icon="i-heroicons-plus" @click="showMeetingForm = true">Schedule</UButton>
            </div>
            <div v-if="meetings.length === 0" class="text-center text-gray-500 py-8">No meetings scheduled</div>
            <div v-for="meeting in meetings" :key="meeting.id" class="border rounded-lg p-4">
              <div class="flex justify-between items-start mb-2">
                <div>
                  <span class="font-medium">{{ meeting.title }}</span>
                  <UBadge :color="getMeetingStatusColor(meeting.status)" size="xs" class="ml-2">{{ meeting.status }}</UBadge>
                </div>
                <UBadge variant="outline" size="xs">{{ meeting.meeting_type }}</UBadge>
              </div>
              <div class="text-sm text-gray-600">
                <div><UIcon name="i-heroicons-calendar" class="inline mr-1" />{{ formatDate(meeting.start_time) }}</div>
                <div v-if="meeting.location"><UIcon name="i-heroicons-map-pin" class="inline mr-1" />{{ meeting.location }}</div>
              </div>
            </div>
          </div>

          <!-- Documents Tab -->
          <div v-if="item.key === 'documents'" class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="font-semibold">Documents</h3>
              <UButton size="sm" icon="i-heroicons-plus" @click="showDocForm = true">Upload</UButton>
            </div>
            <div v-if="documents.length === 0" class="text-center text-gray-500 py-8">No documents uploaded</div>
            <div class="grid grid-cols-2 gap-4">
              <div v-for="doc in documents" :key="doc.id" class="flex items-center gap-3 p-3 border rounded-lg">
                <UIcon name="i-heroicons-document" class="text-2xl text-gray-400" />
                <div class="flex-1 min-w-0">
                  <div class="font-medium truncate">{{ doc.name }}</div>
                  <div class="text-xs text-gray-500">{{ doc.category }} • {{ formatBytes(doc.file_size) }}</div>
                </div>
                <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="deleteDocument(doc.id)" />
              </div>
            </div>
          </div>
        </UCard>
      </template>
    </UTabs>

    <!-- Email Form Modal -->
    <UModal v-model="showEmailForm">
      <UCard>
        <template #header><h3 class="font-semibold">Compose Email</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Subject"><UInput v-model="emailForm.subject" /></UFormGroup>
          <UFormGroup label="To"><UInput v-model="emailForm.to_email" :placeholder="customer?.email" /></UFormGroup>
          <UFormGroup label="Message"><UTextarea v-model="emailForm.body" rows="5" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" @click="showEmailForm = false">Cancel</UButton>
            <UButton @click="sendEmail" :loading="saving">Send</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Call Form Modal -->
    <UModal v-model="showCallForm">
      <UCard>
        <template #header><h3 class="font-semibold">Log Call</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Direction">
            <USelectMenu v-model="callForm.direction" :options="['outgoing', 'incoming']" />
          </UFormGroup>
          <UFormGroup label="Phone"><UInput v-model="callForm.phone_number" :placeholder="customer?.phone" /></UFormGroup>
          <UFormGroup label="Duration (seconds)"><UInput v-model.number="callForm.duration" type="number" /></UFormGroup>
          <UFormGroup label="Status">
            <USelectMenu v-model="callForm.status" :options="['completed', 'missed', 'voicemail']" />
          </UFormGroup>
          <UFormGroup label="Notes"><UTextarea v-model="callForm.notes" rows="3" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" @click="showCallForm = false">Cancel</UButton>
            <UButton @click="logCall" :loading="saving">Save</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Meeting Form Modal -->
    <UModal v-model="showMeetingForm">
      <UCard>
        <template #header><h3 class="font-semibold">Schedule Meeting</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Title"><UInput v-model="meetingForm.title" /></UFormGroup>
          <UFormGroup label="Type">
            <USelectMenu v-model="meetingForm.meeting_type" :options="['in_person', 'virtual', 'phone']" />
          </UFormGroup>
          <div class="grid grid-cols-2 gap-4">
            <UFormGroup label="Start Time"><UInput v-model="meetingForm.start_time" type="datetime-local" /></UFormGroup>
            <UFormGroup label="Location"><UInput v-model="meetingForm.location" /></UFormGroup>
          </div>
          <UFormGroup label="Description"><UTextarea v-model="meetingForm.description" rows="3" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" @click="showMeetingForm = false">Cancel</UButton>
            <UButton @click="scheduleMeeting" :loading="saving">Schedule</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Document Form Modal -->
    <UModal v-model="showDocForm">
      <UCard>
        <template #header><h3 class="font-semibold">Add Document</h3></template>
        <div class="space-y-4">
          <UFormGroup label="Name"><UInput v-model="docForm.name" /></UFormGroup>
          <UFormGroup label="Category">
            <USelectMenu v-model="docForm.category" :options="['contract', 'proposal', 'invoice', 'other']" />
          </UFormGroup>
          <UFormGroup label="File Path"><UInput v-model="docForm.file_path" placeholder="/path/to/file.pdf" /></UFormGroup>
          <UFormGroup label="Description"><UTextarea v-model="docForm.description" rows="2" /></UFormGroup>
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" @click="showDocForm = false">Cancel</UButton>
            <UButton @click="addDocument" :loading="saving">Add</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const { $api } = useNuxtApp()
const toast = useToast()

definePageMeta({ middleware: 'auth' })

const customerId = computed(() => route.params.id as string)
const activeTab = ref(0)
const saving = ref(false)

const customer = ref<any>(null)
const emails = ref([])
const calls = ref([])
const meetings = ref([])
const documents = ref([])

const showEmailForm = ref(false)
const showCallForm = ref(false)
const showMeetingForm = ref(false)
const showDocForm = ref(false)

const tabs = [
    { key: 'emails', label: 'Emails', icon: 'i-heroicons-envelope' },
    { key: 'calls', label: 'Calls', icon: 'i-heroicons-phone' },
    { key: 'meetings', label: 'Meetings', icon: 'i-heroicons-calendar' },
    { key: 'documents', label: 'Documents', icon: 'i-heroicons-document' }
]

const emailForm = reactive({ subject: '', body: '', to_email: '', direction: 'outgoing' })
const callForm = reactive({ direction: 'outgoing', phone_number: '', duration: 0, status: 'completed', notes: '' })
const meetingForm = reactive({ title: '', meeting_type: 'in_person', start_time: '', location: '', description: '' })
const docForm = reactive({ name: '', category: 'other', file_path: '', description: '' })

const formatCurrency = (val: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(val || 0)
const formatDate = (d: string) => d ? new Date(d).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' }) : '-'
const formatDuration = (sec: number) => { const m = Math.floor(sec / 60); const s = sec % 60; return `${m}m ${s}s` }
const formatBytes = (b: number) => b ? (b / 1024).toFixed(1) + ' KB' : '-'
const getMeetingStatusColor = (s: string) => ({ scheduled: 'blue', completed: 'green', cancelled: 'red' }[s] || 'gray')

const fetchCustomer = async () => {
    try {
        const res = await $api.get(`/crm/customers/${customerId.value}`)
        customer.value = res.data?.data
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load customer', color: 'red' }) }
}

const fetchEmails = async () => { try { emails.value = (await $api.get(`/crm/customers/${customerId.value}/emails`)).data?.data || [] } catch(e) {} }
const fetchCalls = async () => { try { calls.value = (await $api.get(`/crm/customers/${customerId.value}/calls`)).data?.data || [] } catch(e) {} }
const fetchMeetings = async () => { try { meetings.value = (await $api.get(`/crm/customers/${customerId.value}/meetings`)).data?.data || [] } catch(e) {} }
const fetchDocuments = async () => { try { documents.value = (await $api.get(`/crm/customers/${customerId.value}/documents`)).data?.data || [] } catch(e) {} }

const editCustomer = () => navigateTo(`/crm/customers?edit=${customerId.value}`)

const sendEmail = async () => {
    saving.value = true
    try {
        await $api.post(`/crm/customers/${customerId.value}/emails`, emailForm)
        toast.add({ title: 'Sent', description: 'Email sent' })
        showEmailForm.value = false; fetchEmails()
        Object.assign(emailForm, { subject: '', body: '', to_email: '' })
    } catch(e) { toast.add({ title: 'Error', description: 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const logCall = async () => {
    saving.value = true
    try {
        await $api.post(`/crm/customers/${customerId.value}/calls`, callForm)
        toast.add({ title: 'Saved', description: 'Call logged' })
        showCallForm.value = false; fetchCalls()
        Object.assign(callForm, { direction: 'outgoing', phone_number: '', duration: 0, status: 'completed', notes: '' })
    } catch(e) { toast.add({ title: 'Error', description: 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const scheduleMeeting = async () => {
    saving.value = true
    try {
        await $api.post(`/crm/customers/${customerId.value}/meetings`, meetingForm)
        toast.add({ title: 'Scheduled', description: 'Meeting scheduled' })
        showMeetingForm.value = false; fetchMeetings()
        Object.assign(meetingForm, { title: '', meeting_type: 'in_person', start_time: '', location: '', description: '' })
    } catch(e) { toast.add({ title: 'Error', description: 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const addDocument = async () => {
    saving.value = true
    try {
        await $api.post(`/crm/customers/${customerId.value}/documents`, docForm)
        toast.add({ title: 'Added', description: 'Document added' })
        showDocForm.value = false; fetchDocuments()
        Object.assign(docForm, { name: '', category: 'other', file_path: '', description: '' })
    } catch(e) { toast.add({ title: 'Error', description: 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const deleteDocument = async (id: string) => {
    if (!confirm('Delete this document?')) return
    try {
        await $api.delete(`/crm/documents/${id}`)
        toast.add({ title: 'Deleted', description: 'Document deleted' })
        fetchDocuments()
    } catch(e) { toast.add({ title: 'Error', description: 'Failed', color: 'red' }) }
}

onMounted(() => {
    fetchCustomer()
    fetchEmails()
    fetchCalls()
    fetchMeetings()
    fetchDocuments()
})
</script>
