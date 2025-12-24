<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Project Management Office (PMO)</h2>
      <UButton icon="i-heroicons-plus" color="black" @click="isOpen = true">New Project</UButton>
    </div>

    <!-- Project Cards Grid -->
    <div v-if="loading" class="text-center py-4">Loading projects...</div>
    <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <UCard v-for="project in projects" :key="project.id" class="cursor-pointer hover:ring-2 hover:ring-primary-500 transition-all" @click="goToProject(project.id)">
            <template #header>
                <div class="flex justify-between items-start">
                    <h3 class="font-bold text-lg">{{ project.name }}</h3>
                    <UBadge :color="getStatusColor(project.status)" variant="soft">{{ project.status }}</UBadge>
                </div>
            </template>
            
            <div class="space-y-2 text-sm text-gray-600">
                <div class="flex justify-between">
                   <span>Code:</span> <span class="font-mono font-bold">{{ project.code }}</span>
                </div>
                <div class="flex justify-between">
                   <span>Type:</span> <span>{{ project.type }}</span>
                </div>
                <div class="flex justify-between">
                   <span>Budget:</span> <span class="text-green-600 font-bold">${{ project.budget?.toLocaleString() }}</span>
                </div>
                <div class="pt-2">
                     <div class="flex justify-between text-xs mb-1">
                        <span>Timeline</span>
                        <span>{{ project.start_date ? new Date(project.start_date).toLocaleDateString() : 'TBD' }} - {{ project.end_date ? new Date(project.end_date).toLocaleDateString() : 'TBD' }}</span>
                     </div>
                     <UProgress :value="calculateProgress(project)" color="blue" size="sm" />
                </div>
            </div>
        </UCard>
    </div>

    <!-- Create Project Modal -->
    <UModal v-model="isOpen">
      <div class="p-4">
        <h3 class="text-lg font-bold mb-4">Create New Project</h3>
        <UForm :state="form" class="space-y-4" @submit="onSubmit">
            <UFormGroup label="Project Name" name="name" required hint="Descriptive project name" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="form.name" placeholder="e.g. New Product Development" />
            </UFormGroup>
            <div class="grid grid-cols-2 gap-4">
                <UFormGroup label="Project Code" name="code" required hint="Unique identifier" :ui="{ hint: 'text-xs text-gray-400' }">
                    <UInput v-model="form.code" placeholder="e.g. PRJ-2024-001" />
                </UFormGroup>
                <UFormGroup label="Type" name="type" required hint="Project category" :ui="{ hint: 'text-xs text-gray-400' }">
                    <USelect v-model="form.type" :options="['R_AND_D', 'CUSTOMER_ORDER', 'INTERNAL_IMPROVEMENT']" />
                </UFormGroup>
            </div>
             <UFormGroup label="Budget Estimate" name="budget" required hint="Total project budget" :ui="{ hint: 'text-xs text-gray-400' }">
                <UInput v-model="form.budget" type="number" placeholder="0" />
            </UFormGroup>
            <div class="grid grid-cols-2 gap-4">
                 <UFormGroup label="Start Date" name="start_date" required hint="Project kick-off" :ui="{ hint: 'text-xs text-gray-400' }">
                     <UInput v-model="form.start_date" type="date" />
                </UFormGroup>
                <UFormGroup label="End Date" name="end_date" required hint="Target completion" :ui="{ hint: 'text-xs text-gray-400' }">
                     <UInput v-model="form.end_date" type="date" />
                </UFormGroup>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isOpen = false">Cancel</UButton>
                <UButton type="submit" color="black" :loading="saving" :disabled="!form.name || !form.code">Create Project</UButton>
            </div>
        </UForm>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const router = useRouter()
const toast = useToast()
const loading = ref(false)
const saving = ref(false)
const isOpen = ref(false)
const projects = ref([])

const form = reactive({
    name: '',
    code: '',
    type: 'R_AND_D',
    budget: 0,
    start_date: '',
    end_date: ''
})

const fetchProjects = async () => {
    loading.value = true
    try {
        const res = await $api.get('/projects')
        projects.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

const onSubmit = async () => {
    saving.value = true
    try {
        await $api.post('/projects', form)
        toast.add({ title: 'Success', description: 'Project created.' })
        isOpen.value = false
        fetchProjects()
        // Reset (Partial)
        form.name = ''
        form.code = ''
        form.budget = 0
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to create project.' })
    } finally {
        saving.value = false
    }
}

const goToProject = (id: string) => {
    router.push(`/projects/${id}`)
}

const getStatusColor = (status: string) => {
    switch (status) {
        case 'PLANNING': return 'blue'
        case 'IN_PROGRESS': return 'orange'
        case 'COMPLETED': return 'green'
        case 'CANCELLED': return 'red'
        default: return 'gray'
    }
}

const calculateProgress = (project: any) => {
    // This should ideally come from backend aggregation of tasks
    return 0 // Placeholder
}

onMounted(() => {
    fetchProjects()
})
</script>
