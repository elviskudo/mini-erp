<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between border-b pb-4">
      <div>
          <div class="text-sm text-gray-500 mb-1 cursor-pointer hover:underline" @click="$router.push('/projects')">← Back to Projects</div>
          <h2 class="text-2xl font-bold text-gray-900">{{ project?.name || 'Loading...' }}</h2>
          <div class="flex gap-2 text-sm mt-1">
              <UBadge color="gray" variant="soft">{{ project?.code }}</UBadge>
              <UBadge :color="project?.status === 'IN_PROGRESS' ? 'orange' : 'blue'" variant="soft">{{ project?.status }}</UBadge>
              <UBadge color="green" variant="soft">Budget: ${{ project?.budget?.toLocaleString() }}</UBadge>
              <UBadge :color="(financials?.total_actual_cost || 0) > (project?.budget || 0) ? 'red' : 'green'" variant="outline">
                  Actual: ${{ financials?.total_actual_cost?.toLocaleString() || 0 }}
              </UBadge>
          </div>
      </div>
      <div class="flex gap-2">
           <UButton icon="i-heroicons-arrow-path" color="white" @click="fetchProjectData">Refresh</UButton>
           <UButton icon="i-heroicons-plus" color="black" @click="openTaskModal()">Add Task</UButton>
      </div>
    </div>

    <!-- Gantt Chart Visualization (Simple CSS Grid / Relative implementation) -->
    <UCard class="overflow-x-auto">
        <div class="min-w-[800px]">
            <h3 class="font-bold mb-4">Gantt Chart (WBS)</h3>
            
            <div class="relative border rounded bg-white min-h-[300px] p-4">
                <!-- Timeline Header Placeholders -->
                <div class="flex border-b pb-2 mb-2 text-xs text-gray-400">
                    <div class="w-1/4">Task Name</div>
                    <div class="flex-1 flex justify-between">
                        <span>Start</span>
                        <span>End</span>
                    </div>
                </div>

                <!-- Recursively render tasks or flat list if sorted -->
                 <div v-if="tasks.length === 0" class="text-center text-gray-400 py-10">
                    No tasks yet. Add a task to start planning.
                </div>

                <div v-for="task in tasks" :key="task.id" class="group flex items-center py-2 border-b hover:bg-gray-50 relative">
                     <!-- Task Info -->
                     <div class="w-1/4 pr-4 pl-2 border-r flex flex-col justify-center">
                         <div class="font-medium text-sm truncate" :class="{'pl-4': task.parent_id}">
                             {{ task.wbs_code }} {{ task.name }}
                         </div>
                         <div class="text-xs text-gray-500">{{ task.assigned_to || 'Unassigned' }}</div>
                     </div>

                     <!-- Timeline Bar (Mock Visual) -->
                     <div class="flex-1 px-4 relative h-8 flex items-center">
                         <!-- In a real Gantt, width and left offset would be calculated based on dates relative to project start/end -->
                         <!-- For this demo, we just show a bar and dates -->
                         <div class="h-6 rounded bg-blue-500 opacity-80 relative group-hover:bg-blue-600 transition-colors w-full cursor-grab"
                              :style="{ 
                                  width: getTaskWidth(task), 
                                  marginLeft: getTaskOffset(task) 
                              }">
                              <div class="absolute inset-0 flex items-center justify-center text-xs text-white font-bold">
                                  {{ task.progress }}%
                              </div>
                         </div>
                         <!-- Date Labels outside bar for readability if bar is small, but put inside for now -->
                     </div>
                </div>
            </div>
        </div>
    </UCard>

    <!-- Add/Edit Task Modal -->
    <UModal v-model="isTaskOpen">
      <div class="p-4">
        <h3 class="text-lg font-bold mb-4">Manage Task</h3>
         <UForm :state="taskForm" class="space-y-4" @submit="submitTask">
            <UFormGroup label="Task Name" name="name" required>
                <UInput v-model="taskForm.name" />
            </UFormGroup>
             <div class="grid grid-cols-2 gap-4">
                <UFormGroup label="WBS Code (e.g. 1.1)" name="wbs_code">
                    <UInput v-model="taskForm.wbs_code" />
                </UFormGroup>
                 <UFormGroup label="Progress %" name="progress">
                    <UInput v-model="taskForm.progress" type="number" min="0" max="100" />
                </UFormGroup>
            </div>
            <div class="grid grid-cols-2 gap-4">
                 <UFormGroup label="Start Date" name="start_date">
                     <UInput v-model="taskForm.start_date" type="date" />
                </UFormGroup>
                <UFormGroup label="End Date" name="end_date">
                     <UInput v-model="taskForm.end_date" type="date" />
                </UFormGroup>
            </div>
             <UFormGroup label="Parent Task (Optional)" name="parent_id">
                 <USelectMenu v-model="taskForm.parent_id" 
                              :options="taskOptions" 
                              value-attribute="id"
                              option-attribute="name"
                              placeholder="None (Top Level)" />
            </UFormGroup>

            <div class="flex justify-end gap-2 mt-6">
                <UButton color="gray" variant="ghost" @click="isTaskOpen = false">Cancel</UButton>
                <UButton type="submit" color="black" :loading="saving">Save Task</UButton>
            </div>
        </UForm>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const route = useRoute()
const toast = useToast()

const project = ref(null)
const tasks = ref([])
const financials = ref(null)
const isTaskOpen = ref(false)
const saving = ref(false)

const taskForm = reactive({
    name: '',
    wbs_code: '',
    start_date: '',
    end_date: '',
    progress: 0,
    parent_id: null
})

// Computed for SelectMenu
const taskOptions = computed(() => {
    return tasks.value.map(t => ({ id: t.id, name: `${t.wbs_code || ''} ${t.name}` }))
})

const fetchProjectData = async () => {
    try {
        const [ganttRes, costRes] = await Promise.all([
             $api.get(`/projects/${route.params.id}/gantt`),
             $api.get(`/projects/${route.params.id}/costs`)
        ])
        project.value = ganttRes.data.project
        tasks.value = ganttRes.data.tasks.sort((a, b) => (a.wbs_code || '').localeCompare(b.wbs_code || ''))
        financials.value = costRes.data
    } catch (e) {
        console.error(e)
        // router.push('/projects')
    }
}

const openTaskModal = () => {
    taskForm.name = ''
    taskForm.wbs_code = ''
    taskForm.progress = 0
    taskForm.start_date = ''
    taskForm.end_date = ''
    taskForm.parent_id = null
    isTaskOpen.value = true
}

const submitTask = async () => {
    saving.value = true
    try {
        await $api.post(`/projects/${route.params.id}/tasks`, taskForm)
        toast.add({ title: 'Success', description: 'Task added.' })
        isTaskOpen.value = false
        fetchProjectData()
    } catch (e) {
        toast.add({ title: 'Error', description: 'Failed to add task.' })
    } finally {
        saving.value = false
    }
}

// Simple visualization helpers
// In a real app we'd convert dates to pixels relative to project start/end
const getTaskWidth = (task) => {
    // Just a mock width logic for demo since we don't have a real date-to-pixel scale implementation here
    // In production this would calculate (end - start) / total_duration * 100
    return '50%' 
}

const getTaskOffset = (task) => {
    // Mock offset
    return '0%'
}

onMounted(() => {
    fetchProjectData()
})
</script>
