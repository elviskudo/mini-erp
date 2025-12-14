<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Employees</h2>
      <UButton icon="i-heroicons-plus" color="black" @click="isOpen = true">New Employee</UButton>
    </div>

    <UCard>
       <UTable :columns="columns" :rows="employees" :loading="loading">
            <template #status-data="{ row }">
                <UBadge :color="row.status === 'Active' ? 'green' : 'red'" variant="soft">{{ row.status }}</UBadge>
            </template>
       </UTable>
    </UCard>

    <UModal v-model="isOpen">
      <div class="p-4">
        <h3 class="text-lg font-bold mb-4">Add Employee</h3>
        <UForm :state="form" class="space-y-4" @submit="onSubmit">
            <UFormGroup label="First Name" name="first_name" required>
                <UInput v-model="form.first_name" />
            </UFormGroup>
            <UFormGroup label="Last Name" name="last_name" required>
                <UInput v-model="form.last_name" />
            </UFormGroup>
            <UFormGroup label="Email" name="email" required>
                <UInput v-model="form.email" type="email" />
            </UFormGroup>
             <UFormGroup label="Phone" name="phone">
                <UInput v-model="form.phone" />
            </UFormGroup>
            <div class="grid grid-cols-2 gap-4">
                <UFormGroup label="Department" name="department">
                     <UInput v-model="form.department" />
                </UFormGroup>
                 <UFormGroup label="Job Title" name="job_title">
                     <UInput v-model="form.job_title" />
                </UFormGroup>
            </div>
            <div class="grid grid-cols-2 gap-4">
                 <UFormGroup label="Base Salary" name="base_salary">
                     <UInput v-model="form.base_salary" type="number" />
                </UFormGroup>
                <UFormGroup label="Hire Date" name="hire_date">
                     <UInput v-model="form.hire_date" type="date" />
                </UFormGroup>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" color="black" :loading="saving">Save</UButton>
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
const isOpen = ref(false)
const employees = ref([])

const form = reactive({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    job_title: '',
    base_salary: 5000,
    hire_date: new Date().toISOString().split('T')[0]
})

const columns = [
  { key: 'first_name', label: 'First Name' },
  { key: 'last_name', label: 'Last Name' },
  { key: 'job_title', label: 'Title' },
  { key: 'department', label: 'Dept' },
  { key: 'base_salary', label: 'Salary' },
  { key: 'status', label: 'Status' }
]

const fetchEmployees = async () => {
    loading.value = true
    try {
        const res = await $api.get('/hr/employees')
        employees.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const onSubmit = async () => {
    saving.value = true
    try {
        await $api.post('/hr/employees', form)
        toast.add({ title: 'Success', description: 'Employee created.' })
        isOpen.value = false
        fetchEmployees()
        // Reset form
        Object.assign(form, {
            first_name: '', last_name: '', email: '', phone: '',
            department: '', job_title: '', base_salary: 5000,
            hire_date: new Date().toISOString().split('T')[0]
        })
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to create employee.', color: 'red' })
    } finally {
        saving.value = false
    }
}

onMounted(() => {
    fetchEmployees()
})
</script>
