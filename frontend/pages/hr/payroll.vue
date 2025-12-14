<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Payroll Management</h2>
      <UButton icon="i-heroicons-plus" color="black" @click="isOpen = true">New Pay Period</UButton>
    </div>

    <!-- Periods List -->
    <div v-if="loading" class="text-center py-4">Loading periods...</div>
    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <UCard v-for="period in periods" :key="period.id" :class="period.is_closed ? 'bg-gray-50' : 'border-primary-200'">
            <div class="flex justify-between items-start mb-2">
                <h3 class="font-bold text-lg">{{ period.name }}</h3>
                <UBadge :color="period.is_closed ? 'gray' : 'green'" variant="subtle">
                    {{ period.is_closed ? 'Closed' : 'Open' }}
                </UBadge>
            </div>
            <div class="text-sm text-gray-500 mb-4">
                {{ new Date(period.start_date).toLocaleDateString() }} - {{ new Date(period.end_date).toLocaleDateString() }}
            </div>
            
            <div class="flex justify-end">
                <UButton v-if="!period.is_closed" 
                         block 
                         icon="i-heroicons-play" 
                         :loading="runningPayroll === period.id"
                         @click="runPayroll(period.id)">
                    Run Payroll
                </UButton>
                <UButton v-else block color="gray" variant="ghost" disabled>
                    Paid
                </UButton>
            </div>
        </UCard>
    </div>

    <!-- Create Period Modal -->
    <UModal v-model="isOpen">
      <div class="p-4">
        <h3 class="text-lg font-bold mb-4">New Payroll Period</h3>
        <UForm :state="form" class="space-y-4" @submit="onCreatePeriod">
            <UFormGroup label="Period Name (e.g. March 2024)" name="name" required>
                <UInput v-model="form.name" />
            </UFormGroup>
            <div class="grid grid-cols-2 gap-4">
                 <UFormGroup label="Start Date" name="start_date" required>
                     <UInput v-model="form.start_date" type="date" />
                </UFormGroup>
                <UFormGroup label="End Date" name="end_date" required>
                     <UInput v-model="form.end_date" type="date" />
                </UFormGroup>
            </div>
            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" color="black" :loading="saving">Create</UButton>
            </div>
        </UForm>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const toast = useToast()
const loading = ref(false)
const saving = ref(false)
const runningPayroll = ref<string | null>(null)
const isOpen = ref(false)
const periods = ref([])

const form = reactive({
    name: '',
    start_date: '',
    end_date: ''
})

const fetchPeriods = async () => {
    loading.value = true
    try {
        const res = await $api.get('/hr/payroll/periods')
        periods.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const onCreatePeriod = async () => {
    saving.value = true
    try {
        await $api.post('/hr/payroll/periods', form)
        toast.add({ title: 'Success', description: 'Period created.' })
        isOpen.value = false
        fetchPeriods()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to create period.', color: 'red' })
    } finally {
        saving.value = false
    }
}

const runPayroll = async (periodId: string) => {
    if (!confirm('Are you sure you want to run payroll? This will post expenses to Finance.')) return
    
    runningPayroll.value = periodId
    try {
        await $api.post(`/hr/payroll/run/${periodId}`)
        toast.add({ title: 'Success', description: 'Payroll run completed successfully.' })
        fetchPeriods()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Payroll run failed.', color: 'red' })
    } finally {
        runningPayroll.value = null
    }
}

onMounted(() => {
    fetchPeriods()
})
</script>
