<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Chart of Accounts</h1>
        <p class="text-xs text-gray-500">Manage account structure</p>
      </div>
      <div class="flex gap-2">
        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="sm" @click="fetchAccounts">Refresh</UButton>
        <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Account</UButton>
      </div>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <UInput v-model="search" placeholder="Search account..." icon="i-heroicons-magnifying-glass" size="sm" class="w-64" />
    </UCard>

    <UCard :ui="{ body: { padding: 'p-0' } }">
      <div v-if="loading" class="text-center py-8 text-gray-500">Loading accounts...</div>
      <div v-else class="divide-y divide-gray-100">
        <div v-for="node in filteredAccounts" :key="node.id" 
             class="flex items-center justify-between py-2 px-4 hover:bg-gray-50 cursor-pointer"
             :style="{ paddingLeft: `${(node.level * 20) + 16}px` }"
             @click="openForm(node)">
          <div class="flex items-center gap-3">
            <span class="font-mono text-xs text-primary-600 font-bold w-20">{{ node.code }}</span>
            <span :class="['text-sm', node.level === 0 ? 'font-semibold' : 'font-medium']">{{ node.name }}</span>
          </div>
          <UBadge color="gray" variant="soft" size="xs">{{ node.type }}</UBadge>
        </div>
      </div>
    </UCard>

    <FormSlideover v-model="showForm" :title="editing ? 'Edit Account' : 'New Account'" :loading="saving" @submit="saveAccount">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Define COA structure for financial reporting and transactions.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Account Code" required hint="Unique code, e.g. 1100, 4100" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="1100" size="sm" />
          </UFormGroup>
          <UFormGroup label="Account Type" required hint="Asset, Liability, Equity, Revenue, Expense" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.type" :options="accountTypes" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Account Name" required hint="Descriptive name of the account" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="Cash and Bank" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Parent Account" hint="Select parent for hierarchy, or leave empty for top-level" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.parent_id" :options="parentOptions" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Description" hint="Optional notes about this account's purpose" :ui="{ hint: 'text-xs text-gray-400' }">
          <UTextarea v-model="form.description" rows="2" size="sm" />
        </UFormGroup>
        
        <UCheckbox v-model="form.is_active" label="Active" />
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()

const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const editing = ref(false)
const search = ref('')
const accounts = ref<any[]>([])
const flattenedAccounts = ref<any[]>([])

const accountTypes = ['Asset', 'Liability', 'Equity', 'Revenue', 'Expense']

const parentOptions = computed(() => [
  { label: 'None (Top Level)', value: '' },
  ...flattenedAccounts.value.map(a => ({ label: `${a.code} - ${a.name}`, value: a.id }))
])

const form = reactive({ id: '', code: '', name: '', type: 'Asset', parent_id: '', description: '', is_active: true })

const filteredAccounts = computed(() => {
  if (!search.value) return flattenedAccounts.value
  const s = search.value.toLowerCase()
  return flattenedAccounts.value.filter((a: any) => a.code?.toLowerCase().includes(s) || a.name?.toLowerCase().includes(s))
})

const flattenTree = (nodes: any[], level = 0): any[] => {
  let result: any[] = []
  for (const node of nodes) {
    result.push({ ...node, level })
    if (node.children?.length) result = result.concat(flattenTree(node.children, level + 1))
  }
  return result
}

const fetchAccounts = async () => {
  loading.value = true
  try {
    const res = await $api.get('/finance/coa')
    accounts.value = res.data
    flattenedAccounts.value = flattenTree(res.data)
  } catch {
    flattenedAccounts.value = [
      { id: '1', code: '1000', name: 'Assets', type: 'Asset', level: 0 },
      { id: '2', code: '1100', name: 'Current Assets', type: 'Asset', level: 1 },
      { id: '3', code: '1110', name: 'Cash and Bank', type: 'Asset', level: 2 },
      { id: '4', code: '2000', name: 'Liabilities', type: 'Liability', level: 0 },
      { id: '5', code: '3000', name: 'Equity', type: 'Equity', level: 0 },
      { id: '6', code: '4000', name: 'Revenue', type: 'Revenue', level: 0 },
      { id: '7', code: '5000', name: 'Expenses', type: 'Expense', level: 0 }
    ]
  } finally { loading.value = false }
}

const openForm = (account?: any) => {
  if (account) {
    editing.value = true
    Object.assign(form, { id: account.id, code: account.code, name: account.name, type: account.type, parent_id: account.parent_id || '', description: account.description || '', is_active: account.is_active !== false })
  } else {
    editing.value = false
    Object.assign(form, { id: '', code: '', name: '', type: 'Asset', parent_id: '', description: '', is_active: true })
  }
  showForm.value = true
}

const saveAccount = async () => {
  if (!form.code || !form.name) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try {
    // Convert empty string to null for parent_id
    const payload = {
      ...form,
      parent_id: form.parent_id || null
    }
    if (editing.value) {
      await $api.put(`/finance/coa/${form.id}`, payload)
    } else {
      await $api.post('/finance/coa', payload)
    }
    toast.add({ title: 'Account saved', color: 'green' })
    showForm.value = false
    await fetchAccounts()
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

onMounted(() => fetchAccounts())
</script>
