<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-900">Bank Accounts</h1>
        <p class="text-xs text-gray-500">Manage bank and cash accounts</p>
      </div>
      <UButton icon="i-heroicons-plus" size="sm" @click="openForm()">New Account</UButton>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <UCard v-for="account in accounts" :key="account.id" class="hover:shadow-lg transition-shadow cursor-pointer" @click="viewAccount(account)">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div :class="['p-2 rounded-lg', account.account_type === 'Petty Cash' ? 'bg-yellow-100' : 'bg-blue-100']">
              <UIcon :name="account.account_type === 'Petty Cash' ? 'i-heroicons-banknotes' : 'i-heroicons-building-library'" 
                     :class="['w-5 h-5', account.account_type === 'Petty Cash' ? 'text-yellow-600' : 'text-blue-600']" />
            </div>
            <div>
              <h3 class="font-semibold text-sm text-gray-900">{{ account.name }}</h3>
              <p class="text-xs text-gray-500">{{ account.bank_name }}</p>
              <p class="text-xs text-gray-400 font-mono">{{ account.account_number }}</p>
            </div>
          </div>
          <UBadge :color="account.is_active ? 'green' : 'gray'" variant="soft" size="xs">
            {{ account.is_active ? 'Active' : 'Inactive' }}
          </UBadge>
        </div>
        <div class="mt-3 pt-3 border-t border-gray-100">
          <div class="flex justify-between items-center">
            <span class="text-xs text-gray-500">Current Balance</span>
            <span class="text-lg font-bold text-gray-900">{{ formatCurrencyCompact(account.current_balance) }}</span>
          </div>
        </div>
      </UCard>
    </div>

    <UCard :ui="{ body: { padding: 'p-3' } }">
      <div class="flex justify-between items-center">
        <span class="text-sm font-semibold text-gray-700">Total Cash Position</span>
        <span class="text-xl font-bold text-green-600">{{ formatCurrencyCompact(totalBalance) }}</span>
      </div>
    </UCard>

    <FormSlideover v-model="showForm" :title="editing ? 'Edit Account' : 'New Bank Account'" :loading="saving" @submit="saveAccount">
      <div class="space-y-4">
        <p class="text-xs text-gray-500 pb-2 border-b">Set up a bank or cash account to track balances and transactions.</p>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Account Code" required hint="Unique identifier, e.g. BCA-01" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.code" placeholder="BCA-01" size="sm" />
          </UFormGroup>
          <UFormGroup label="Account Type" required hint="Checking, Savings, Petty Cash, etc." :ui="{ hint: 'text-xs text-gray-400' }">
            <USelectMenu v-model="form.account_type" :options="accountTypes" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Account Name" required hint="Display name for this account" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.name" placeholder="BCA Giro Utama" size="sm" />
        </UFormGroup>
        
        <div class="grid grid-cols-2 gap-3">
          <UFormGroup label="Bank Name" hint="Name of the financial institution" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.bank_name" placeholder="Bank Central Asia" size="sm" />
          </UFormGroup>
          <UFormGroup label="Account Number" hint="Bank account number" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.account_number" placeholder="1234567890" size="sm" />
          </UFormGroup>
        </div>
        
        <UFormGroup label="Account Holder" hint="Name on the bank account" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model="form.account_holder" placeholder="PT Company Name" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="Opening Balance" hint="Initial balance when account was created" :ui="{ hint: 'text-xs text-gray-400' }">
          <UInput v-model.number="form.opening_balance" type="number" size="sm" />
        </UFormGroup>
        
        <UFormGroup label="GL Account" hint="Link to Chart of Accounts for reporting" :ui="{ hint: 'text-xs text-gray-400' }">
          <USelectMenu v-model="form.gl_account_id" :options="glAccounts" option-attribute="label" value-attribute="value" size="sm" />
        </UFormGroup>
        
        <UCheckbox v-model="form.is_active" label="Active" />
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
import { formatCompact } from '~/utils/format'

const { $api } = useNuxtApp()
const toast = useToast()

const saving = ref(false)
const showForm = ref(false)
const editing = ref(false)
const accounts = ref<any[]>([])
const glAccountsList = ref<any[]>([])

const accountTypes = ['Checking', 'Savings', 'Petty Cash', 'Digital Wallet']
const glAccounts = computed(() => [{ label: 'Select GL', value: '' }, ...glAccountsList.value.map(a => ({ label: `${a.code} - ${a.name}`, value: a.id }))])

const form = reactive({ code: '', name: '', bank_name: '', account_number: '', account_holder: '', account_type: 'Checking', opening_balance: 0, gl_account_id: '', is_active: true })

const totalBalance = computed(() => accounts.value.reduce((sum, acc) => sum + (acc.current_balance || 0), 0))
const formatCurrencyCompact = (amount: number) => `Rp ${formatCompact(amount)}`

const fetchAccounts = async () => {
  try {
    const res = await $api.get('/finance/banking/accounts')
    accounts.value = res.data
  } catch {
    accounts.value = [
      { id: '1', code: 'BCA-01', name: 'BCA Giro Utama', bank_name: 'Bank Central Asia', account_number: '1234567890', account_type: 'Checking', current_balance: 250000000, is_active: true },
      { id: '2', code: 'MDR-01', name: 'Mandiri Operasional', bank_name: 'Bank Mandiri', account_number: '9876543210', account_type: 'Checking', current_balance: 85000000, is_active: true },
      { id: '3', code: 'PC-01', name: 'Petty Cash Office', bank_name: '-', account_number: '-', account_type: 'Petty Cash', current_balance: 5000000, is_active: true }
    ]
  }
}

const fetchGLAccounts = async () => { try { glAccountsList.value = (await $api.get('/finance/coa')).data } catch {} }

const openForm = (account?: any) => {
  if (account) {
    editing.value = true
    Object.assign(form, account)
  } else {
    editing.value = false
    Object.assign(form, { code: '', name: '', bank_name: '', account_number: '', account_holder: '', account_type: 'Checking', opening_balance: 0, gl_account_id: '', is_active: true })
  }
  showForm.value = true
}

const viewAccount = (acc: any) => navigateTo(`/finance/banking/transactions?account=${acc.id}`)

const saveAccount = async () => {
  if (!form.code || !form.name) { toast.add({ title: 'Fill required fields', color: 'red' }); return }
  saving.value = true
  try {
    if (editing.value) await $api.put(`/finance/banking/accounts/${form.id}`, form)
    else await $api.post('/finance/banking/accounts', form)
    toast.add({ title: 'Account saved', color: 'green' })
    showForm.value = false
    await fetchAccounts()
  } catch (e: any) { toast.add({ title: e.response?.data?.detail || 'Failed', color: 'red' }) }
  finally { saving.value = false }
}

onMounted(() => { fetchAccounts(); fetchGLAccounts() })
</script>
