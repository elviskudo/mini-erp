<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div class="flex items-center gap-4">
        <UButton icon="i-heroicons-arrow-left" variant="ghost" color="gray" @click="router.back()" />
        <div>
          <div class="flex items-center gap-3">
            <h2 class="text-xl font-bold">{{ project?.name }}</h2>
            <UBadge v-if="project" :color="getStatusColor(project.status)" variant="subtle">{{ formatStatus(project.status) }}</UBadge>
          </div>
          <p class="text-gray-500 text-sm font-mono">{{ project?.code }}</p>
        </div>
      </div>
      <div class="flex gap-2">
        <UButton variant="ghost" icon="i-heroicons-arrow-path" @click="fetchAll">Refresh</UButton>
        <UButton icon="i-heroicons-pencil" @click="openEditProject">Edit</UButton>
        <UButton color="red" variant="outline" icon="i-heroicons-trash" @click="deleteProject">Delete</UButton>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-12">
      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin text-gray-400" />
    </div>

    <template v-else-if="project">
      <!-- Stats -->
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <UCard :ui="{ body: { padding: 'p-4' } }"><div class="text-center"><p class="text-2xl font-bold">{{ stats.progress_percentage || 0 }}%</p><p class="text-sm text-gray-500">Progress</p></div></UCard>
        <UCard :ui="{ body: { padding: 'p-4' } }"><div class="text-center"><p class="text-2xl font-bold text-blue-600">{{ stats.completed_tasks || 0 }}/{{ stats.task_count || 0 }}</p><p class="text-sm text-gray-500">Tasks Done</p></div></UCard>
        <UCard :ui="{ body: { padding: 'p-4' } }"><div class="text-center"><p class="text-2xl font-bold text-purple-600">{{ stats.team_size || 0 }}</p><p class="text-sm text-gray-500">Team Size</p></div></UCard>
        <UCard :ui="{ body: { padding: 'p-4' } }"><div class="text-center"><p class="text-2xl font-bold text-orange-600">{{ stats.total_actual_hours || 0 }}h</p><p class="text-sm text-gray-500">Hours Logged</p></div></UCard>
        <UCard :ui="{ body: { padding: 'p-4' } }"><div class="text-center"><p class="text-2xl font-bold" :class="(stats.budget_remaining || 0) >= 0 ? 'text-green-600' : 'text-red-600'">{{ formatShortCurrency(stats.budget_remaining || 0) }}</p><p class="text-sm text-gray-500">Budget Left</p></div></UCard>
      </div>

      <!-- Tabs -->
      <UCard>
        <UTabs :items="tabs" v-model="activeTab">
          <template #overview>
            <div class="grid md:grid-cols-3 gap-6 pt-4">
              <div class="md:col-span-2 space-y-4">
                <div><h4 class="font-semibold text-gray-700 mb-2">Description</h4><p class="text-gray-600">{{ project.description || 'No description' }}</p></div>
                <div class="grid grid-cols-2 gap-4">
                  <div><p class="text-sm text-gray-500">Type</p><p class="font-medium">{{ formatType(project.type) }}</p></div>
                  <div><p class="text-sm text-gray-500">Priority</p><UBadge :color="getPriorityColor(project.priority)">{{ project.priority }}</UBadge></div>
                  <div><p class="text-sm text-gray-500">Start</p><p class="font-medium">{{ formatDate(project.start_date) }}</p></div>
                  <div><p class="text-sm text-gray-500">End</p><p class="font-medium">{{ formatDate(project.end_date) }}</p></div>
                  <div><p class="text-sm text-gray-500">Budget</p><p class="font-medium text-green-600">{{ formatCurrency(project.budget) }}</p></div>
                  <div><p class="text-sm text-gray-500">Expenses</p><p class="font-medium text-red-600">{{ formatCurrency(stats.total_expenses || 0) }}</p></div>
                </div>
              </div>
              <div>
                <div class="flex justify-between items-center mb-3"><h4 class="font-semibold text-gray-700">Team</h4><UButton size="xs" icon="i-heroicons-plus" @click="openAddMember">Add</UButton></div>
                <div class="space-y-2">
                  <div v-for="m in members" :key="m.id" class="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                    <div class="flex items-center gap-2"><UAvatar :alt="m.user_name" size="sm" /><div><p class="font-medium text-sm">{{ m.user_name }}</p><p class="text-xs text-gray-500">{{ formatRole(m.role) }}</p></div></div>
                    <UButton size="xs" color="red" variant="ghost" icon="i-heroicons-x-mark" @click="removeMember(m)" />
                  </div>
                  <p v-if="members.length === 0" class="text-sm text-gray-400 text-center py-4">No members</p>
                </div>
              </div>
            </div>
          </template>

          <!-- Tasks Tab - Kanban with Drag & Drop -->
          <template #tasks>
            <div class="pt-4 space-y-4">
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-2">
                  <UButton :variant="viewMode === 'kanban' ? 'solid' : 'ghost'" size="xs" icon="i-heroicons-view-columns" @click="viewMode = 'kanban'" />
                  <UButton :variant="viewMode === 'list' ? 'solid' : 'ghost'" size="xs" icon="i-heroicons-list-bullet" @click="viewMode = 'list'" />
                </div>
                <UButton icon="i-heroicons-plus" size="sm" @click="openTaskSlideover()">Add Task</UButton>
              </div>

              <!-- Kanban Board -->
              <div v-if="viewMode === 'kanban'" class="grid grid-cols-5 gap-3 overflow-x-auto pb-4">
                <div 
                  v-for="col in kanbanColumns" 
                  :key="col.status" 
                  class="bg-gray-50 rounded-lg p-2 min-w-[200px]"
                  @dragover.prevent 
                  @drop="onDrop($event, col.status)"
                >
                  <div class="flex items-center gap-2 mb-3 px-1">
                    <div class="w-2 h-2 rounded-full" :class="col.dotColor"></div>
                    <h5 class="font-semibold text-sm">{{ col.label }}</h5>
                    <span class="text-xs bg-gray-200 px-1.5 py-0.5 rounded-full ml-auto">{{ getTasksByStatus(col.status).length }}</span>
                  </div>
                  <div class="space-y-2 min-h-[300px]">
                    <div 
                      v-for="task in getTasksByStatus(col.status)" 
                      :key="task.id" 
                      draggable="true"
                      @dragstart="onDragStart($event, task)"
                      @dragend="onDragEnd"
                      class="bg-white p-3 rounded-lg shadow-sm cursor-grab hover:shadow-md transition-all border border-gray-100 group/card"
                      :class="{ 'opacity-50': draggingTaskId === task.id }"
                    >
                      <div class="flex justify-between items-start mb-1">
                        <p class="font-medium text-sm flex-1">{{ task.name }}</p>
                        <UButton 
                          size="2xs" 
                          variant="ghost" 
                          icon="i-heroicons-eye" 
                          class="opacity-0 group-hover/card:opacity-100 shrink-0"
                          @click.stop="openTaskDetail(task)" 
                        />
                      </div>
                      <div class="flex items-center justify-between mb-2">
                        <span class="text-xs text-gray-400 font-mono">{{ task.wbs_code || '-' }}</span>
                        <UBadge :color="getPriorityColor(task.priority)" size="xs">{{ task.priority }}</UBadge>
                      </div>
                      <!-- Assignees -->
                      <div class="flex items-center gap-1 mt-2">
                        <div v-for="a in getTaskAssignees(task.id)" :key="a.user_id" class="relative group">
                          <UAvatar :alt="a.user_name" size="2xs" />
                          <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10">{{ a.user_name }}</div>
                        </div>
                        <span v-if="task.estimated_hours" class="text-xs text-gray-400 ml-auto"><UIcon name="i-heroicons-clock" class="w-3 h-3 inline" /> {{ task.estimated_hours }}h</span>
                      </div>
                    </div>
                    <div v-if="getTasksByStatus(col.status).length === 0" class="text-center py-8 text-gray-300 text-xs">Drop here</div>
                  </div>
                </div>
              </div>

              <!-- List View -->
              <div v-else class="divide-y">
                <div v-for="task in tasks" :key="task.id" class="py-3 flex items-center justify-between group">
                  <div class="flex items-center gap-3 flex-1">
                    <UCheckbox :model-value="task.status === 'DONE'" @change="toggleTask(task)" />
                    <div class="flex-1 cursor-pointer" @click="openTaskDetail(task)">
                      <p :class="['font-medium', task.status === 'DONE' ? 'line-through text-gray-400' : '']">{{ task.name }}</p>
                      <div class="flex items-center gap-3 text-xs text-gray-500"><span v-if="task.wbs_code" class="font-mono">{{ task.wbs_code }}</span><span>{{ task.estimated_hours || 0 }}h</span></div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <div v-for="a in getTaskAssignees(task.id)" :key="a.user_id"><UAvatar :alt="a.user_name" size="2xs" /></div>
                    <UBadge :color="getTaskStatusColor(task.status)" size="xs">{{ task.status }}</UBadge>
                    <UButton size="xs" variant="ghost" icon="i-heroicons-pencil" class="opacity-0 group-hover:opacity-100" @click="openTaskSlideover(task)" />
                    <UButton size="xs" variant="ghost" color="red" icon="i-heroicons-trash" class="opacity-0 group-hover:opacity-100" @click="deleteTask(task)" />
                  </div>
                </div>
                <div v-if="tasks.length === 0" class="py-8 text-center text-gray-400">No tasks yet</div>
              </div>
            </div>
          </template>

          <template #time>
            <div class="pt-4 space-y-4">
              <div class="flex justify-end"><UButton icon="i-heroicons-plus" size="sm" @click="openTimeSlideover">Log Time</UButton></div>
              <UTable :columns="timeColumns" :rows="timeEntries" :empty-state="{ icon: 'i-heroicons-clock', label: 'No entries' }">
                <template #date-data="{ row }">{{ formatDate(row.date) }}</template>
                <template #hours-data="{ row }"><span class="font-semibold">{{ row.hours }}h</span></template>
              </UTable>
            </div>
          </template>

          <template #expenses>
            <div class="pt-4 space-y-4">
              <div class="flex justify-end"><UButton icon="i-heroicons-plus" size="sm" @click="openExpenseSlideover">Add Expense</UButton></div>
              <UTable :columns="expenseColumns" :rows="expenses" :empty-state="{ icon: 'i-heroicons-banknotes', label: 'No expenses' }">
                <template #date-data="{ row }">{{ formatDate(row.date) }}</template>
                <template #amount-data="{ row }"><span class="font-semibold text-red-600">{{ formatCurrency(row.amount) }}</span></template>
              </UTable>
            </div>
          </template>
        </UTabs>
      </UCard>
    </template>

    <!-- Member Slideover -->
    <FormSlideover v-model="isMemberSlideoverOpen" title="Add Team Member" :loading="saving" @submit="addMember">
      <UFormGroup label="User" required><USelect v-model="memberForm.user_id" :options="userOptions" placeholder="Select user" /></UFormGroup>
      <UFormGroup label="Role"><USelect v-model="memberForm.role" :options="roleOptions" /></UFormGroup>
      <UFormGroup label="Hourly Rate (IDR)"><UInput v-model.number="memberForm.hourly_rate" type="number" /></UFormGroup>
    </FormSlideover>

    <!-- Task Slideover -->
    <FormSlideover v-model="isTaskSlideoverOpen" :title="editingTask ? 'Edit Task' : 'Add Task'" :loading="saving" @submit="saveTask">
      <UFormGroup label="Task Name" required><UInput v-model="taskForm.name" placeholder="Task name" /></UFormGroup>
      <UFormGroup label="Description"><UTextarea v-model="taskForm.description" :rows="2" /></UFormGroup>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="WBS Code"><UInput v-model="taskForm.wbs_code" placeholder="1.1" /></UFormGroup>
        <UFormGroup label="Est. Hours"><UInput v-model.number="taskForm.estimated_hours" type="number" step="0.5" /></UFormGroup>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Status"><USelect v-model="taskForm.status" :options="taskStatusSelectOptions" /></UFormGroup>
        <UFormGroup label="Priority"><USelect v-model="taskForm.priority" :options="priorityOptions" /></UFormGroup>
      </div>
      <!-- Multi-user assignment -->
      <UFormGroup label="Assign To" hint="Select multiple users">
        <USelectMenu v-model="taskForm.assignee_ids" :options="userOptions" multiple placeholder="Select assignees" value-attribute="value" option-attribute="label" />
      </UFormGroup>
    </FormSlideover>

    <USlideover v-model="isTaskDetailOpen" :ui="{ width: 'max-w-lg' }">
      <div class="p-6 space-y-4 overflow-y-auto max-h-screen" v-if="selectedTask">
        <div class="flex justify-between items-start">
          <h3 class="text-lg font-bold">Task Details</h3>
          <UButton icon="i-heroicons-x-mark" variant="ghost" color="gray" @click="isTaskDetailOpen = false" />
        </div>

        <!-- Editable Fields -->
        <UFormGroup label="Title">
          <UInput v-model="taskDetailForm.name" />
        </UFormGroup>
        <UFormGroup label="Description">
          <div class="border rounded-lg overflow-hidden">
            <!-- Toolbar -->
            <div class="flex gap-1 p-2 bg-gray-50 border-b">
              <button type="button" @click="formatText('bold')" class="p-1.5 rounded hover:bg-gray-200" title="Bold"><b>B</b></button>
              <button type="button" @click="formatText('italic')" class="p-1.5 rounded hover:bg-gray-200" title="Italic"><i>I</i></button>
              <button type="button" @click="formatText('underline')" class="p-1.5 rounded hover:bg-gray-200" title="Underline"><u>U</u></button>
              <button type="button" @click="formatText('insertUnorderedList')" class="p-1.5 rounded hover:bg-gray-200" title="Bullet List">•</button>
              <button type="button" @click="formatText('insertOrderedList')" class="p-1.5 rounded hover:bg-gray-200" title="Number List">1.</button>
            </div>
            <!-- Editor -->
            <div 
              ref="descriptionEditor"
              contenteditable="true"
              class="min-h-[100px] p-3 focus:outline-none prose prose-sm max-w-none"
              @input="onDescriptionInput"
              v-html="taskDetailForm.description"
            ></div>
          </div>
        </UFormGroup>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Status">
            <USelect v-model="taskDetailForm.status" :options="taskStatusSelectOptions" />
          </UFormGroup>
          <UFormGroup label="Priority">
            <USelect v-model="taskDetailForm.priority" :options="priorityOptions" />
          </UFormGroup>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UFormGroup label="Start Date">
            <UInput v-model="taskDetailForm.start_date" type="date" />
          </UFormGroup>
          <UFormGroup label="End Date">
            <UInput v-model="taskDetailForm.end_date" type="date" />
          </UFormGroup>
        </div>
        <UButton block @click="saveTaskDetail" :loading="saving">Save Changes</UButton>

        <UDivider />

        <!-- Attachments -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <h4 class="font-semibold text-sm">Attachments</h4>
            <label class="cursor-pointer">
              <UButton size="xs" icon="i-heroicons-arrow-up-tray" @click="triggerFileUpload">Upload</UButton>
              <input ref="fileInput" type="file" class="hidden" accept="image/*,.pdf,.doc,.docx,.xls,.xlsx" @change="handleFileUpload" />
            </label>
          </div>
          <div class="space-y-2">
            <div v-for="att in taskAttachments" :key="att.id" class="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
              <a :href="att.file_url" target="_blank" class="flex items-center gap-2 text-sm hover:underline text-blue-600">
                <UIcon :name="getFileIcon(att.file_type)" class="w-4 h-4" />
                {{ att.file_name }}
              </a>
              <UButton size="2xs" variant="ghost" color="red" icon="i-heroicons-trash" @click="deleteAttachment(att.id)" />
            </div>
            <p v-if="taskAttachments.length === 0" class="text-xs text-gray-400">No attachments</p>
          </div>
          <div v-if="uploading" class="mt-2 text-sm text-gray-500"><UIcon name="i-heroicons-arrow-path" class="w-4 h-4 animate-spin inline mr-1" /> Uploading...</div>
        </div>
        
        <UDivider />

        <!-- Assignees -->
        <div>
          <div class="flex justify-between items-center mb-2"><h4 class="font-semibold text-sm">Assignees</h4><UButton size="xs" icon="i-heroicons-plus" @click="openAssigneeModal">Add</UButton></div>
          <div class="flex flex-wrap gap-2">
            <div v-for="a in taskAssignees" :key="a.user_id" class="flex items-center gap-1 bg-gray-100 rounded-full px-2 py-1">
              <UAvatar :alt="a.user_name" size="2xs" /><span class="text-xs">{{ a.user_name }}</span>
              <UButton size="2xs" variant="ghost" color="red" icon="i-heroicons-x-mark" @click="removeAssignee(a.user_id)" />
            </div>
            <p v-if="taskAssignees.length === 0" class="text-xs text-gray-400">No assignees</p>
          </div>
        </div>

        <UDivider />

        <!-- Comments with Reactions and Replies -->
        <div>
          <h4 class="font-semibold text-sm mb-2">Comments</h4>
          <div class="space-y-3 max-h-64 overflow-y-auto mb-3">
            <template v-for="c in rootComments" :key="c.id">
              <div class="bg-gray-50 rounded-lg p-3">
                <div class="flex justify-between items-start">
                  <div class="flex items-center gap-2">
                    <UAvatar :alt="c.user_name" size="2xs" />
                    <span class="font-medium text-sm">{{ c.user_name }}</span>
                    <span class="text-xs text-gray-400">{{ formatDateTime(c.created_at) }}</span>
                  </div>
                  <UButton size="2xs" variant="ghost" color="red" icon="i-heroicons-trash" @click="deleteComment(c.id)" />
                </div>
                <p class="text-sm mt-1">{{ c.content }}</p>
                <!-- Reactions -->
                <div class="flex items-center gap-2 mt-2">
                  <button v-for="r in reactionTypes" :key="r.key" @click="toggleReaction(c.id, r.key)" 
                    class="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs transition-colors"
                    :class="hasReacted(c, r.key) ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 hover:bg-gray-200'">
                    <span>{{ r.emoji }}</span>
                    <span>{{ getReactionCount(c, r.key) }}</span>
                  </button>
                  <button @click="replyingTo = replyingTo === c.id ? null : c.id" class="text-xs text-gray-500 hover:text-blue-600 ml-2">Reply</button>
                </div>
                <!-- Reply input -->
                <div v-if="replyingTo === c.id" class="flex gap-2 mt-2">
                  <UInput v-model="replyContent" placeholder="Write a reply..." size="xs" class="flex-1" @keyup.enter="sendReply(c.id)" />
                  <UButton size="xs" @click="sendReply(c.id)">Send</UButton>
                </div>
                <!-- Replies -->
                <div v-if="getReplies(c.id).length > 0" class="ml-4 mt-2 space-y-2">
                  <div v-for="reply in getReplies(c.id)" :key="reply.id" class="bg-white p-2 rounded border-l-2 border-blue-200">
                    <div class="flex justify-between items-start">
                      <div class="flex items-center gap-2">
                        <UAvatar :alt="reply.user_name" size="2xs" />
                        <span class="font-medium text-xs">{{ reply.user_name }}</span>
                        <span class="text-xs text-gray-400">{{ formatDateTime(reply.created_at) }}</span>
                      </div>
                      <UButton size="2xs" variant="ghost" color="red" icon="i-heroicons-trash" @click="deleteComment(reply.id)" />
                    </div>
                    <p class="text-xs mt-1">{{ reply.content }}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <button v-for="r in reactionTypes" :key="r.key" @click="toggleReaction(reply.id, r.key)" 
                        class="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs transition-colors"
                        :class="hasReacted(reply, r.key) ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 hover:bg-gray-200'">
                        <span>{{ r.emoji }}</span>
                        <span>{{ getReactionCount(reply, r.key) }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            <p v-if="taskComments.length === 0" class="text-xs text-gray-400">No comments yet</p>
          </div>
          <div class="flex gap-2">
            <UInput v-model="newComment" placeholder="Add a comment..." class="flex-1" @keyup.enter="addComment" />
            <UButton icon="i-heroicons-paper-airplane" @click="addComment" />
          </div>
        </div>
      </div>
    </USlideover>

    <!-- Assignee Modal -->
    <UModal v-model="isAssigneeModalOpen">
      <UCard><template #header><h4 class="font-semibold">Add Assignee</h4></template>
        <USelectMenu v-model="selectedAssigneeId" :options="userOptions" placeholder="Select user" value-attribute="value" option-attribute="label" />
        <template #footer><UButton @click="addAssignee" :loading="saving">Add</UButton></template>
      </UCard>
    </UModal>

    <!-- Time Slideover -->
    <FormSlideover v-model="isTimeSlideoverOpen" title="Log Time" :loading="saving" @submit="saveTimeEntry">
      <UFormGroup label="Date" required><UInput v-model="timeForm.date" type="date" /></UFormGroup>
      <UFormGroup label="Hours" required><UInput v-model.number="timeForm.hours" type="number" step="0.5" /></UFormGroup>
      <UFormGroup label="Task"><USelect v-model="timeForm.task_id" :options="taskOptions" placeholder="Link to task" /></UFormGroup>
      <UFormGroup label="Description"><UTextarea v-model="timeForm.description" :rows="2" /></UFormGroup>
    </FormSlideover>

    <!-- Expense Slideover -->
    <FormSlideover v-model="isExpenseSlideoverOpen" title="Add Expense" :loading="saving" @submit="saveExpense">
      <UFormGroup label="Description" required><UInput v-model="expenseForm.description" /></UFormGroup>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Amount (IDR)" required><UInput v-model.number="expenseForm.amount" type="number" /></UFormGroup>
        <UFormGroup label="Category"><USelect v-model="expenseForm.category" :options="expenseCategories" /></UFormGroup>
      </div>
      <UFormGroup label="Date" required><UInput v-model="expenseForm.date" type="date" /></UFormGroup>
    </FormSlideover>

    <!-- Edit Project Slideover -->
    <FormSlideover v-model="isEditSlideoverOpen" title="Edit Project" :loading="saving" @submit="saveProject">
      <UFormGroup label="Name" required><UInput v-model="projectForm.name" /></UFormGroup>
      <UFormGroup label="Description"><UTextarea v-model="projectForm.description" :rows="2" /></UFormGroup>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Code"><UInput v-model="projectForm.code" /></UFormGroup>
        <UFormGroup label="Status"><USelect v-model="projectForm.status" :options="statusOptions" /></UFormGroup>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Priority"><USelect v-model="projectForm.priority" :options="priorityOptions" /></UFormGroup>
        <UFormGroup label="Budget"><UInput v-model.number="projectForm.budget" type="number" /></UFormGroup>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <UFormGroup label="Start Date"><UInput v-model="projectForm.start_date" type="date" /></UFormGroup>
        <UFormGroup label="End Date"><UInput v-model="projectForm.end_date" type="date" /></UFormGroup>
      </div>
    </FormSlideover>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const toast = useToast()
const { $api } = useNuxtApp()

definePageMeta({ layout: 'default' })

const projectId = route.params.id as string

const loading = ref(true)
const saving = ref(false)
const project = ref<any>(null)
const stats = ref<any>({})
const tasks = ref<any[]>([])
const members = ref<any[]>([])
const timeEntries = ref<any[]>([])
const expenses = ref<any[]>([])
const users = ref<any[]>([])
const allAssignees = ref<any[]>([])

const activeTab = ref(0)
const viewMode = ref<'kanban' | 'list'>('kanban')
const editingTask = ref<any>(null)
const draggingTaskId = ref<string | null>(null)

// Slideover states
const isMemberSlideoverOpen = ref(false)
const isTaskSlideoverOpen = ref(false)
const isTimeSlideoverOpen = ref(false)
const isExpenseSlideoverOpen = ref(false)
const isEditSlideoverOpen = ref(false)
const isTaskDetailOpen = ref(false)
const isAssigneeModalOpen = ref(false)

const selectedTask = ref<any>(null)
const taskAssignees = ref<any[]>([])
const taskComments = ref<any[]>([])
const taskAttachments = ref<any[]>([])
const newComment = ref('')
const selectedAssigneeId = ref('')
const replyingTo = ref<string | null>(null)
const replyContent = ref('')
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const descriptionEditor = ref<HTMLDivElement | null>(null)

// Reaction types
const reactionTypes = [
  { key: 'like', emoji: '👍' },
  { key: 'love', emoji: '❤️' },
  { key: 'amazing', emoji: '🤩' }
]

// Forms
const memberForm = reactive({ user_id: '', role: 'MEMBER', hourly_rate: 0 })
const taskForm = reactive({ name: '', description: '', wbs_code: '', status: 'TODO', priority: 'MEDIUM', estimated_hours: 0, assignee_ids: [] as string[] })
const timeForm = reactive({ date: new Date().toISOString().split('T')[0], hours: 1, task_id: '', description: '' })
const expenseForm = reactive({ description: '', amount: 0, category: 'OTHER', date: new Date().toISOString().split('T')[0] })
const projectForm = reactive({ name: '', description: '', code: '', status: 'DRAFT', priority: 'MEDIUM', budget: 0, start_date: '', end_date: '' })
const taskDetailForm = reactive({ name: '', description: '', status: 'TODO', priority: 'MEDIUM', start_date: '', end_date: '' })

// Options
const tabs = [{ label: 'Overview', slot: 'overview' }, { label: 'Tasks', slot: 'tasks' }, { label: 'Time', slot: 'time' }, { label: 'Expenses', slot: 'expenses' }]
const taskStatusSelectOptions = [{ label: 'To Do', value: 'TODO' }, { label: 'In Progress', value: 'IN_PROGRESS' }, { label: 'Review', value: 'REVIEW' }, { label: 'Done', value: 'DONE' }, { label: 'Blocked', value: 'BLOCKED' }]
const priorityOptions = [{ label: 'Low', value: 'LOW' }, { label: 'Medium', value: 'MEDIUM' }, { label: 'High', value: 'HIGH' }, { label: 'Urgent', value: 'URGENT' }]
const statusOptions = [{ label: 'Draft', value: 'DRAFT' }, { label: 'Planning', value: 'PLANNING' }, { label: 'In Progress', value: 'IN_PROGRESS' }, { label: 'Completed', value: 'COMPLETED' }]
const expenseCategories = [{ label: 'Material', value: 'MATERIAL' }, { label: 'Labor', value: 'LABOR' }, { label: 'Equipment', value: 'EQUIPMENT' }, { label: 'Travel', value: 'TRAVEL' }, { label: 'Software', value: 'SOFTWARE' }, { label: 'Other', value: 'OTHER' }]
const roleOptions = [{ label: 'Project Manager', value: 'PROJECT_MANAGER' }, { label: 'Team Lead', value: 'TEAM_LEAD' }, { label: 'Developer', value: 'DEVELOPER' }, { label: 'Designer', value: 'DESIGNER' }, { label: 'QA', value: 'QA' }, { label: 'Member', value: 'MEMBER' }]

const kanbanColumns = [
  { status: 'TODO', label: 'To Do', dotColor: 'bg-gray-400' },
  { status: 'IN_PROGRESS', label: 'In Progress', dotColor: 'bg-blue-500' },
  { status: 'REVIEW', label: 'Review', dotColor: 'bg-purple-500' },
  { status: 'DONE', label: 'Done', dotColor: 'bg-green-500' },
  { status: 'BLOCKED', label: 'Blocked', dotColor: 'bg-red-500' }
]

const timeColumns = [{ key: 'date', label: 'Date' }, { key: 'user_name', label: 'User' }, { key: 'hours', label: 'Hours' }, { key: 'description', label: 'Description' }]
const expenseColumns = [{ key: 'date', label: 'Date' }, { key: 'description', label: 'Description' }, { key: 'category', label: 'Category' }, { key: 'amount', label: 'Amount' }]

const taskOptions = computed(() => [{ label: 'No Task', value: '' }, ...tasks.value.map(t => ({ label: t.name, value: t.id }))])
const userOptions = computed(() => users.value.map(u => ({ label: u.username, value: u.id })))
const getTasksByStatus = (status: string) => tasks.value.filter(t => t.status === status)
const getTaskAssignees = (taskId: string) => allAssignees.value.filter(a => a.task_id === taskId)

// WYSIWYG helpers
const formatText = (command: string) => {
  document.execCommand(command, false)
  descriptionEditor.value?.focus()
}
const onDescriptionInput = (event: Event) => {
  const target = event.target as HTMLDivElement
  taskDetailForm.description = target.innerHTML
}

// Drag & Drop
const onDragStart = (e: DragEvent, task: any) => { draggingTaskId.value = task.id; e.dataTransfer?.setData('text/plain', task.id) }
const onDragEnd = () => { draggingTaskId.value = null }
const onDrop = async (e: DragEvent, newStatus: string) => {
  const taskId = e.dataTransfer?.getData('text/plain')
  if (!taskId) return
  const task = tasks.value.find(t => t.id === taskId)
  if (task && task.status !== newStatus) {
    await $api.put(`/projects/tasks/${taskId}`, { status: newStatus })
    task.status = newStatus
    toast.add({ title: 'Task moved' })
    fetchAll()
  }
}

const fetchAll = async () => {
  loading.value = true
  try {
    const [projectRes, statsRes, tasksRes, membersRes, timeRes, expensesRes, usersRes] = await Promise.all([
      $api.get(`/projects/${projectId}`), $api.get(`/projects/${projectId}/stats`), $api.get(`/projects/${projectId}/tasks`),
      $api.get(`/projects/${projectId}/members`), $api.get(`/projects/${projectId}/time-entries`), $api.get(`/projects/${projectId}/expenses`),
      $api.get('/users').catch(() => ({ data: [] }))
    ])
    project.value = projectRes.data; stats.value = statsRes.data; tasks.value = tasksRes.data
    members.value = membersRes.data; timeEntries.value = timeRes.data; expenses.value = expensesRes.data; users.value = usersRes.data
    // Fetch all assignees for all tasks
    const assigneePromises = tasksRes.data.map((t: any) => $api.get(`/projects/tasks/${t.id}/assignees`).catch(() => ({ data: [] })))
    const assigneeResults = await Promise.all(assigneePromises)
    allAssignees.value = assigneeResults.flatMap(r => r.data)
  } catch (e) { toast.add({ title: 'Error loading project', color: 'red' }) } finally { loading.value = false }
}

// Member
const openAddMember = () => { Object.assign(memberForm, { user_id: '', role: 'MEMBER', hourly_rate: 0 }); isMemberSlideoverOpen.value = true }
const addMember = async () => { if (!memberForm.user_id) return; saving.value = true; try { await $api.post(`/projects/${projectId}/members`, memberForm); isMemberSlideoverOpen.value = false; fetchAll() } catch (e) {} finally { saving.value = false } }
const removeMember = async (m: any) => { if (confirm('Remove?')) { await $api.delete(`/projects/${projectId}/members/${m.user_id}`); fetchAll() } }

// Task
const openTaskSlideover = (task: any = null) => {
  editingTask.value = task
  const currentAssignees = task ? getTaskAssignees(task.id).map(a => a.user_id) : []
  Object.assign(taskForm, task ? { name: task.name, description: task.description || '', wbs_code: task.wbs_code || '', status: task.status, priority: task.priority, estimated_hours: task.estimated_hours || 0, assignee_ids: currentAssignees } : { name: '', description: '', wbs_code: '', status: 'TODO', priority: 'MEDIUM', estimated_hours: 0, assignee_ids: [] })
  isTaskSlideoverOpen.value = true
}
const saveTask = async () => {
  if (!taskForm.name) return; saving.value = true
  try {
    const payload = { name: taskForm.name, description: taskForm.description, wbs_code: taskForm.wbs_code, status: taskForm.status, priority: taskForm.priority, estimated_hours: taskForm.estimated_hours }
    let taskId = editingTask.value?.id
    if (editingTask.value) await $api.put(`/projects/tasks/${taskId}`, payload)
    else { const res = await $api.post(`/projects/${projectId}/tasks`, payload); taskId = res.data.id }
    // Update assignees
    const currentAssignees = getTaskAssignees(taskId).map(a => a.user_id)
    for (const uid of taskForm.assignee_ids) { if (!currentAssignees.includes(uid)) await $api.post(`/projects/tasks/${taskId}/assignees`, { user_id: uid }) }
    for (const uid of currentAssignees) { if (!taskForm.assignee_ids.includes(uid)) await $api.delete(`/projects/tasks/${taskId}/assignees/${uid}`) }
    isTaskSlideoverOpen.value = false; fetchAll()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) } finally { saving.value = false }
}
const toggleTask = async (task: any) => { await $api.put(`/projects/tasks/${task.id}`, { status: task.status === 'DONE' ? 'TODO' : 'DONE' }); fetchAll() }
const deleteTask = async (task: any) => { if (confirm('Delete?')) { await $api.delete(`/projects/tasks/${task.id}`); fetchAll() } }

// Task Detail
const openTaskDetail = async (task: any) => {
  selectedTask.value = task
  // Populate editable form
  Object.assign(taskDetailForm, {
    name: task.name || '',
    description: task.description || '',
    status: task.status || 'TODO',
    priority: task.priority || 'MEDIUM',
    start_date: task.start_date?.split('T')[0] || '',
    end_date: task.end_date?.split('T')[0] || ''
  })
  isTaskDetailOpen.value = true
  const [assigneesRes, commentsRes] = await Promise.all([
    $api.get(`/projects/tasks/${task.id}/assignees`),
    $api.get(`/projects/tasks/${task.id}/comments`)
  ])
  taskAssignees.value = assigneesRes.data
  taskComments.value = commentsRes.data
  // Fetch attachments
  const attachmentsRes = await $api.get(`/projects/tasks/${task.id}/attachments`).catch(() => ({ data: [] }))
  taskAttachments.value = attachmentsRes.data
}
const saveTaskDetail = async () => {
  if (!selectedTask.value) return
  saving.value = true
  try {
    const payload: any = {
      name: taskDetailForm.name,
      description: taskDetailForm.description,
      status: taskDetailForm.status,
      priority: taskDetailForm.priority
    }
    if (taskDetailForm.start_date) payload.start_date = new Date(taskDetailForm.start_date).toISOString()
    if (taskDetailForm.end_date) payload.end_date = new Date(taskDetailForm.end_date).toISOString()
    await $api.put(`/projects/tasks/${selectedTask.value.id}`, payload)
    toast.add({ title: 'Task updated successfully' })
    fetchAll()
  } catch (e) {
    toast.add({ title: 'Error updating task', color: 'red' })
  } finally {
    saving.value = false
  }
}
const openAssigneeModal = () => { selectedAssigneeId.value = ''; isAssigneeModalOpen.value = true }
const addAssignee = async () => {
  if (!selectedAssigneeId.value || !selectedTask.value) return; saving.value = true
  try { await $api.post(`/projects/tasks/${selectedTask.value.id}/assignees`, { user_id: selectedAssigneeId.value }); isAssigneeModalOpen.value = false; openTaskDetail(selectedTask.value); fetchAll() }
  catch (e) { toast.add({ title: 'Already assigned', color: 'orange' }) } finally { saving.value = false }
}
const removeAssignee = async (userId: string) => { if (!selectedTask.value) return; await $api.delete(`/projects/tasks/${selectedTask.value.id}/assignees/${userId}`); openTaskDetail(selectedTask.value); fetchAll() }
const addComment = async () => {
  if (!newComment.value.trim() || !selectedTask.value) return
  await $api.post(`/projects/tasks/${selectedTask.value.id}/comments`, { content: newComment.value })
  newComment.value = ''; openTaskDetail(selectedTask.value)
}

// Comment replies helpers
const rootComments = computed(() => taskComments.value.filter(c => !c.parent_id))
const getReplies = (commentId: string) => taskComments.value.filter(c => c.parent_id === commentId)
const sendReply = async (parentId: string) => {
  if (!replyContent.value.trim() || !selectedTask.value) return
  await $api.post(`/projects/tasks/${selectedTask.value.id}/comments/${parentId}/reply`, { content: replyContent.value })
  replyContent.value = ''; replyingTo.value = null; openTaskDetail(selectedTask.value)
}

// Reactions helpers
const hasReacted = (comment: any, reactionType: string) => {
  const reactions = comment.reactions || {}
  return (reactions[reactionType] || []).includes(String(useNuxtApp().$userId || ''))
}
const getReactionCount = (comment: any, reactionType: string) => {
  const reactions = comment.reactions || {}
  return (reactions[reactionType] || []).length
}
const toggleReaction = async (commentId: string, reactionType: string) => {
  if (!selectedTask.value) return
  await $api.post(`/projects/tasks/${selectedTask.value.id}/comments/${commentId}/react`, { reaction: reactionType })
  openTaskDetail(selectedTask.value)
}

// File upload helpers
const getFileIcon = (fileType: string) => {
  if (fileType?.includes('image')) return 'i-heroicons-photo'
  if (fileType?.includes('pdf')) return 'i-heroicons-document'
  if (fileType?.includes('word') || fileType?.includes('doc')) return 'i-heroicons-document-text'
  if (fileType?.includes('excel') || fileType?.includes('sheet')) return 'i-heroicons-table-cells'
  return 'i-heroicons-paper-clip'
}
const triggerFileUpload = () => { fileInput.value?.click() }
const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !selectedTask.value) return
  
  uploading.value = true
  try {
    // Upload to Cloudinary via unsigned preset (configure in Cloudinary dashboard)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('upload_preset', 'mini_erp_unsigned')  // Configure this in Cloudinary
    
    const cloudinaryRes = await fetch('https://api.cloudinary.com/v1_1/YOUR_CLOUD_NAME/auto/upload', {
      method: 'POST',
      body: formData
    })
    const cloudinaryData = await cloudinaryRes.json()
    
    if (cloudinaryData.secure_url) {
      // Save to backend
      await $api.post(`/projects/tasks/${selectedTask.value.id}/attachments`, {
        file_name: file.name,
        file_url: cloudinaryData.secure_url,
        file_type: file.type,
        file_size: file.size,
        public_id: cloudinaryData.public_id
      })
      toast.add({ title: 'File uploaded!' })
      openTaskDetail(selectedTask.value)
    } else {
      toast.add({ title: 'Upload failed', color: 'red' })
    }
  } catch (e) {
    toast.add({ title: 'Upload error', color: 'red' })
  } finally {
    uploading.value = false
    input.value = ''  // Reset input
  }
}
const deleteAttachment = async (attachmentId: string) => {
  if (!selectedTask.value) return
  await $api.delete(`/projects/tasks/${selectedTask.value.id}/attachments/${attachmentId}`)
  openTaskDetail(selectedTask.value)
}
const deleteComment = async (commentId: string) => { if (!selectedTask.value) return; await $api.delete(`/projects/tasks/${selectedTask.value.id}/comments/${commentId}`); openTaskDetail(selectedTask.value) }

// Time
const openTimeSlideover = () => { Object.assign(timeForm, { date: new Date().toISOString().split('T')[0], hours: 1, task_id: '', description: '' }); isTimeSlideoverOpen.value = true }
const saveTimeEntry = async () => { if (!timeForm.hours) return; saving.value = true; try { await $api.post(`/projects/${projectId}/time-entries`, { ...timeForm, task_id: timeForm.task_id || null }); isTimeSlideoverOpen.value = false; fetchAll() } catch (e) {} finally { saving.value = false } }

// Expense
const openExpenseSlideover = () => { Object.assign(expenseForm, { description: '', amount: 0, category: 'OTHER', date: new Date().toISOString().split('T')[0] }); isExpenseSlideoverOpen.value = true }
const saveExpense = async () => { if (!expenseForm.description || !expenseForm.amount) return; saving.value = true; try { await $api.post(`/projects/${projectId}/expenses`, expenseForm); isExpenseSlideoverOpen.value = false; fetchAll() } catch (e) {} finally { saving.value = false } }

// Project
const openEditProject = () => { Object.assign(projectForm, { name: project.value.name, description: project.value.description || '', code: project.value.code, status: project.value.status, priority: project.value.priority, budget: project.value.budget || 0, start_date: project.value.start_date?.split('T')[0] || '', end_date: project.value.end_date?.split('T')[0] || '' }); isEditSlideoverOpen.value = true }
const saveProject = async () => {
  saving.value = true; try {
    const payload = { ...projectForm }
    if (payload.start_date) payload.start_date = new Date(payload.start_date).toISOString()
    if (payload.end_date) payload.end_date = new Date(payload.end_date).toISOString()
    await $api.put(`/projects/${projectId}`, payload); isEditSlideoverOpen.value = false; fetchAll()
  } catch (e) { toast.add({ title: 'Error', color: 'red' }) } finally { saving.value = false }
}
const deleteProject = async () => { if (confirm('Delete project?')) { await $api.delete(`/projects/${projectId}`); router.push('/projects') } }

// Formatters
const getStatusColor = (s: string) => ({ DRAFT: 'gray', PLANNING: 'blue', IN_PROGRESS: 'orange', ON_HOLD: 'yellow', COMPLETED: 'green', CANCELLED: 'red' }[s] || 'gray')
const getTaskStatusColor = (s: string) => ({ TODO: 'gray', IN_PROGRESS: 'blue', REVIEW: 'purple', DONE: 'green', BLOCKED: 'red' }[s] || 'gray')
const getPriorityColor = (p: string) => ({ LOW: 'gray', MEDIUM: 'blue', HIGH: 'orange', URGENT: 'red' }[p] || 'gray')
const formatStatus = (s: string) => s?.split('_').map(w => w.charAt(0) + w.slice(1).toLowerCase()).join(' ') || ''
const formatType = (t: string) => ({ R_AND_D: 'R&D', CUSTOMER_ORDER: 'Customer', INTERNAL_IMPROVEMENT: 'Internal', MAINTENANCE: 'Maintenance', CONSULTING: 'Consulting' }[t] || t)
const formatRole = (r: string) => r?.split('_').map(w => w.charAt(0) + w.slice(1).toLowerCase()).join(' ') || ''
const formatCurrency = (v: number) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(v || 0)
const formatShortCurrency = (v: number) => { const a = Math.abs(v || 0); const s = v < 0 ? '-' : ''; if (a >= 1e9) return s + (a / 1e9).toFixed(1) + 'B'; if (a >= 1e6) return s + (a / 1e6).toFixed(1) + 'M'; if (a >= 1e3) return s + (a / 1e3).toFixed(1) + 'k'; return s + a }
const formatDate = (d: string) => d ? new Date(d).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const formatDateTime = (d: string) => d ? new Date(d).toLocaleString('id-ID', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-'

onMounted(fetchAll)
</script>
