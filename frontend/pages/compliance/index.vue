<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Compliance & QMS</h2>
    </div>

    <!-- Tabs -->
    <UTabs :items="tabs" class="w-full">
        <template #audit="{ item }">
            <UCard>
                <div class="flex gap-2 mb-4">
                     <UInput v-model="auditSearch.username" placeholder="Search by User..." />
                     <UInput v-model="auditSearch.action" placeholder="Search Action..." />
                     <UButton icon="i-heroicons-magnifying-glass" color="black" @click="fetchAuditLogs">Search</UButton>
                </div>

                <UTable :columns="auditColumns" :rows="auditLogs" :loading="loadingAudit">
                     <template #timestamp-data="{ row }">
                        <span class="font-mono text-xs">{{ new Date(row.timestamp).toLocaleString() }}</span>
                    </template>
                     <template #details-data="{ row }">
                        <span class="text-xs text-gray-500 truncate max-w-xs block" :title="JSON.stringify(row.details || {})">
                            {{ JSON.stringify(row.details || {}) }}
                        </span>
                    </template>
                </UTable>
            </UCard>
        </template>

        <template #sops="{ item }">
             <UCard>
                <div class="flex justify-between mb-4">
                    <h3 class="font-bold">SOP Documents</h3>
                     <UButton icon="i-heroicons-plus" color="black" @click="isSopOpen = true">New SOP</UButton>
                </div>
                
                 <UTable :columns="sopColumns" :rows="sops" :loading="loadingSops">
                    <template #status-data="{ row }">
                        <UBadge :color="row.status === 'APPROVED' ? 'green' : 'orange'" variant="subtle">{{ row.status }}</UBadge>
                    </template>
                    <template #actions-data="{ row }">
                        <UButton v-if="row.status === 'DRAFT'" size="xs" color="green" variant="ghost" @click="approveSop(row)">Approve</UButton>
                         <UButton v-if="row.file_url" size="xs" color="blue" variant="ghost" icon="i-heroicons-document-text" :to="row.file_url" target="_blank">View</UButton>
                    </template>
                </UTable>
             </UCard>
        </template>
    </UTabs>

    <!-- Create SOP Modal -->
    <UModal v-model="isSopOpen">
      <div class="p-4">
        <h3 class="text-lg font-bold mb-4">Create SOP Document</h3>
         <UForm :state="sopForm" class="space-y-4" @submit="submitSop">
            <UFormGroup label="Title" name="title" required>
                <UInput v-model="sopForm.title" />
            </UFormGroup>
            <UFormGroup label="Content / Description" name="content">
                <UTextarea v-model="sopForm.content" />
            </UFormGroup>
            <UFormGroup label="File URL (Simulated)" name="file_url">
                <UInput v-model="sopForm.file_url" placeholder="https://..." />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isSopOpen = false">Cancel</UButton>
                <UButton type="submit" color="black" :loading="savingSop">Create Draft</UButton>
            </div>
        </UForm>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

const tabs = [
    { slot: 'audit', label: 'Audit Trail Logs' },
    { slot: 'sops', label: 'Document Control (SOPs)' }
]

// Audit Logic
const loadingAudit = ref(false)
const auditLogs = ref([])
const auditSearch = reactive({ username: '', action: '' })
const auditColumns = [
    { key: 'timestamp', label: 'Time' },
    { key: 'username', label: 'User' },
    { key: 'action', label: 'Action' },
    { key: 'method', label: 'Method' },
    { key: 'path', label: 'Path' },
    { key: 'details', label: 'Details' }
]

const fetchAuditLogs = async () => {
    loadingAudit.value = true
    try {
        const params = { ...auditSearch }
        const res = await $api.get('/compliance/audit-logs', { params })
        auditLogs.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loadingAudit.value = false
    }
}

// SOP Logic
const loadingSops = ref(false)
const sops = ref([])
const isSopOpen = ref(false)
const savingSop = ref(false)
const sopForm = reactive({ title: '', content: '', file_url: '' })
const sopColumns = [
    { key: 'title', label: 'Title' },
    { key: 'version', label: 'Ver' },
    { key: 'status', label: 'Status' },
    { key: 'effective_date', label: 'Effective' },
    { key: 'actions', label: 'Actions' }
]

const fetchSops = async () => {
    loadingSops.value = true
    try {
        const res = await $api.get('/compliance/sops')
        sops.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loadingSops.value = false
    }
}

const submitSop = async () => {
    savingSop.value = true
    try {
        // Query param hack for simplified POST in router
        await $api.post('/compliance/sops', null, { params: sopForm })
        toast.add({ title: 'Success', description: 'SOP Draft created.' })
        isSopOpen.value = false
        fetchSops()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to create SOP.' })
    } finally {
        savingSop.value = false
    }
}

const approveSop = async (row) => {
    try {
        await $api.patch(`/compliance/sops/${row.id}/approve`)
        toast.add({ title: 'Approved', description: 'SOP is now Effective.' })
        fetchSops()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to approve.' })
    }
}

onMounted(() => {
    fetchAuditLogs()
    fetchSops()
})
</script>
