<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Approval Rules</h2>
        <p class="text-gray-500">Atur siapa yang bisa meng-approve request dari role tertentu</p>
      </div>
      <UButton icon="i-heroicons-arrow-left" variant="ghost" to="/procurement/requests">Kembali ke PR</UButton>
    </div>

    <!-- Add Rule Card -->
    <UCard>
      <template #header>
        <h3 class="font-medium">Tambah Aturan Baru</h3>
      </template>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UFormGroup label="Request dari Role" required hint="Role yang membuat request" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.requester_role" :options="roles" option-attribute="label" value-attribute="value" placeholder="Pilih role requester" />
        </UFormGroup>
        <UFormGroup label="Bisa di-approve oleh" required hint="Role yang bisa menyetujui" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelect v-model="form.approver_role" :options="roles" option-attribute="label" value-attribute="value" placeholder="Pilih role approver" />
        </UFormGroup>
        <UFormGroup label="Deskripsi" hint="Keterangan aturan (opsional)" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.description" placeholder="Contoh: Staff butuh approval Manager" />
        </UFormGroup>
      </div>
      <template #footer>
        <div class="flex justify-end">
          <UButton :loading="submitting" :disabled="!form.requester_role || !form.approver_role" @click="addRule">Tambah Aturan</UButton>
        </div>
      </template>
    </UCard>

    <!-- Rules Table -->
    <UCard :ui="{ body: { padding: '' } }">
      <template #header>
        <h3 class="font-medium">Daftar Aturan Approval</h3>
      </template>
      <UTable :columns="columns" :rows="rules" :loading="loading">
        <template #requester_role-data="{ row }">
          <UBadge color="blue" variant="subtle">{{ row.requester_role }}</UBadge>
        </template>
        <template #approver_role-data="{ row }">
          <UBadge color="green" variant="subtle">{{ row.approver_role }}</UBadge>
        </template>
        <template #actions-data="{ row }">
          <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click="deleteRule(row.id)" />
        </template>
      </UTable>
      <div v-if="!rules.length" class="p-8 text-center text-gray-500">
        <span class="i-heroicons-shield-exclamation text-4xl mb-2 block"></span>
        Belum ada aturan approval
      </div>
    </UCard>

    <!-- Example Card -->
    <UCard class="bg-blue-50 border-blue-200">
      <div class="flex items-start gap-3">
        <span class="i-heroicons-light-bulb text-2xl text-blue-600"></span>
        <div>
          <h4 class="font-medium text-blue-900">Contoh Penggunaan</h4>
          <ul class="mt-2 text-sm text-blue-800 space-y-1">
            <li>• <b>STAFF → FINANCE</b>: Staff bisa di-approve oleh Finance</li>
            <li>• <b>STAFF → MANAGER</b>: Staff juga bisa di-approve oleh Manager</li>
            <li>• <b>FINANCE → MANAGER</b>: Finance hanya bisa di-approve oleh Manager</li>
          </ul>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const authStore = useAuthStore()
const toast = useToast()
const loading = ref(false)
const submitting = ref(false)
const rules = ref<any[]>([])
const roles = ref<any[]>([])

const form = reactive({
  requester_role: '',
  approver_role: '',
  description: ''
})

const columns = [
  { key: 'requester_role', label: 'Request dari' },
  { key: 'approver_role', label: 'Approver' },
  { key: 'description', label: 'Deskripsi' },
  { key: 'actions', label: '' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    rules.value = await $fetch('/api/settings/approval-rules', { headers })
    roles.value = await $fetch('/api/settings/roles', { headers })
  } catch (e) {
    toast.add({ title: 'Error', description: 'Gagal memuat data', color: 'red' })
  } finally {
    loading.value = false
  }
}

const addRule = async () => {
  if (!form.requester_role || !form.approver_role) {
    toast.add({ title: 'Error', description: 'Pilih kedua role', color: 'red' })
    return
  }
  submitting.value = true
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch('/api/settings/approval-rules', {
      method: 'POST',
      headers,
      body: form
    })
    toast.add({ title: 'Berhasil', description: 'Aturan ditambahkan', color: 'green' })
    form.requester_role = ''
    form.approver_role = ''
    form.description = ''
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Gagal menambah aturan', color: 'red' })
  } finally {
    submitting.value = false
  }
}

const deleteRule = async (id: string) => {
  if (!confirm('Hapus aturan ini?')) return
  try {
    const headers = { Authorization: `Bearer ${authStore.token}` }
    await $fetch(`/api/settings/approval-rules/${id}`, { method: 'DELETE', headers })
    toast.add({ title: 'Dihapus', description: 'Aturan dihapus' })
    fetchData()
  } catch (e) {
    toast.add({ title: 'Error', description: 'Gagal menghapus', color: 'red' })
  }
}

onMounted(fetchData)
</script>
