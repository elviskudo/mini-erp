<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Web Forms</h1>
        <p class="text-gray-500">Create lead capture forms for your website</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openCreate">New Form</UButton>
    </div>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <ServerDataTable :columns="columns" :data="items" :loading="loading" :pagination="pagination" @page-change="handlePageChange">
        <template #slug-data="{ row }">
          <code class="text-xs bg-gray-100 px-2 py-1 rounded">{{ row.slug }}</code>
        </template>
        <template #submissions-data="{ row }">
          <UBadge color="blue" variant="subtle">{{ row.submissions || 0 }} submissions</UBadge>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'active' ? 'green' : 'gray'" variant="subtle">{{ row.status }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton icon="i-heroicons-eye" color="gray" variant="ghost" size="xs" @click="viewSubmissions(row)" />
            <UButton icon="i-heroicons-pencil" color="gray" variant="ghost" size="xs" @click="openEdit(row)" />
            <UButton icon="i-heroicons-trash" color="red" variant="ghost" size="xs" @click="confirmDelete(row)" />
          </div>
        </template>
      </ServerDataTable>
    </UCard>

    <FormSlideover v-model="isOpen" :title="editMode ? 'Edit Form' : 'New Form'" :loading="saving" @submit="save">
      <div class="space-y-4">
        <UFormGroup label="Form Name" required>
          <UInput v-model="form.name" placeholder="Contact Us Form" />
        </UFormGroup>
        <UFormGroup label="Description">
          <UTextarea v-model="form.description" rows="2" />
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="URL Slug" required>
            <UInput v-model="form.slug" placeholder="contact-us" />
          </UFormGroup>
          <UFormGroup label="Status">
            <USelectMenu v-model="form.status" :options="['draft', 'active', 'inactive']" />
          </UFormGroup>
        </div>
        <UFormGroup label="Link to Campaign">
          <USelectMenu v-model="form.campaign_id" :options="campaignOptions" value-attribute="value" option-attribute="label" searchable placeholder="None" />
        </UFormGroup>
        <UFormGroup label="Submit Button Text">
          <UInput v-model="form.submit_text" placeholder="Submit" />
        </UFormGroup>
        <UFormGroup label="Success Message">
          <UTextarea v-model="form.success_message" rows="2" placeholder="Thank you for your submission!" />
        </UFormGroup>
        <UFormGroup label="Redirect URL (Optional)">
          <UInput v-model="form.redirect_url" placeholder="https://example.com/thank-you" />
        </UFormGroup>
        
        <div class="border-t pt-4">
          <div class="flex justify-between items-center mb-3">
            <h4 class="font-medium text-sm">Form Fields (JSON)</h4>
          </div>
          <UTextarea v-model="form.fields" rows="6" placeholder='[{"name":"email","type":"email","label":"Email","required":true}]' class="font-mono text-xs" />
          <p class="text-xs text-gray-500 mt-1">Define fields as JSON array with name, type, label, required</p>
        </div>
      </div>
    </FormSlideover>

    <!-- Submissions Modal -->
    <UModal v-model="showSubmissions" :ui="{ width: 'max-w-4xl' }">
      <UCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="font-semibold">Submissions: {{ selectedForm?.name }}</h3>
            <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="showSubmissions = false" />
          </div>
        </template>
        <div v-if="submissions.length">
          <div v-for="sub in submissions" :key="sub.id" class="border-b py-3">
            <div class="text-xs text-gray-500 mb-1">{{ new Date(sub.created_at).toLocaleString() }}</div>
            <pre class="text-xs bg-gray-50 p-2 rounded overflow-auto">{{ sub.data }}</pre>
          </div>
        </div>
        <div v-else class="text-center text-gray-500 py-8">No submissions yet</div>
      </UCard>
    </UModal>
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
const showSubmissions = ref(false)

const items = ref([])
const campaigns = ref<any[]>([])
const submissions = ref([])
const selectedForm = ref<any>(null)
const pagination = ref(null)
const currentPage = ref(1)

const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'slug', label: 'Slug' },
    { key: 'submissions', label: 'Submissions' },
    { key: 'status', label: 'Status' },
    { key: 'actions', label: '' }
]

const campaignOptions = computed(() => [{ label: 'None', value: '' }, ...campaigns.value.map(c => ({ label: c.name, value: c.id }))])

const form = reactive({
    id: '', name: '', description: '', slug: '', campaign_id: '', status: 'draft',
    fields: '[]', submit_text: 'Submit', success_message: 'Thank you for your submission!', redirect_url: ''
})

const fetchData = async () => {
    loading.value = true
    try {
        const res = await $api.get('/crm/forms', { params: { page: currentPage.value } })
        items.value = res.data?.data || []
        pagination.value = res.data?.meta?.pagination
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to load', color: 'red' }) }
    finally { loading.value = false }
    loadCampaigns()
}

const loadCampaigns = async () => {
    try { campaigns.value = (await $api.get('/crm/campaigns', { params: { limit: 100 } })).data?.data || [] } catch(e) {}
}

const viewSubmissions = async (row: any) => {
    selectedForm.value = row
    try {
        const res = await $api.get(`/crm/forms/${row.id}/submissions`)
        submissions.value = res.data?.data || []
    } catch(e) { submissions.value = [] }
    showSubmissions.value = true
}

const handlePageChange = (p: number) => { currentPage.value = p; fetchData() }
const openCreate = () => { resetForm(); editMode.value = false; isOpen.value = true }
const openEdit = (row: any) => { resetForm(); editMode.value = true; Object.assign(form, row); isOpen.value = true }
const resetForm = () => { Object.assign(form, { id: '', name: '', description: '', slug: '', campaign_id: '', status: 'draft', fields: '[]', submit_text: 'Submit', success_message: 'Thank you for your submission!', redirect_url: '' }) }

const save = async () => {
    if (!form.name || !form.slug) return toast.add({ title: 'Error', description: 'Name and slug required', color: 'red' })
    saving.value = true
    try {
        if (editMode.value) await $api.put(`/crm/forms/${form.id}`, form)
        else await $api.post('/crm/forms', form)
        toast.add({ title: 'Saved', description: 'Web form saved.' })
        isOpen.value = false; fetchData(); resetForm()
    } catch(e: any) { toast.add({ title: 'Error', description: e.response?.data?.message || 'Failed', color: 'red' }) }
    finally { saving.value = false }
}

const confirmDelete = async (row: any) => {
    if (!confirm(`Delete form "${row.name}"?`)) return
    try {
        await $api.delete(`/crm/forms/${row.id}`)
        toast.add({ title: 'Deleted', description: 'Form deleted.' })
        fetchData()
    } catch(e) { toast.add({ title: 'Error', description: 'Failed to delete', color: 'red' }) }
}

onMounted(() => fetchData())
</script>
