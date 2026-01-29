<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">User Management</h1>
        <p class="text-gray-500 dark:text-gray-400">Manage users in your organization</p>
      </div>
      <UButton icon="i-heroicons-plus" @click="openAddUser">Add User</UButton>
    </div>

    <!-- Users Table -->
    <UCard :ui="{ body: { padding: 'p-4' } }">
      <DataTable 
        :rows="users" 
        :columns="columns" 
        :loading="loading"
        search-placeholder="Search users..."
      >
        <template #role-data="{ row }">
          <UBadge :color="getRoleColor(row.role)" variant="soft">{{ row.role }}</UBadge>
        </template>
        <template #is_verified-data="{ row }">
          <UBadge :color="row.is_verified ? 'green' : 'amber'" variant="soft">
            {{ row.is_verified ? 'Verified' : 'Pending' }}
          </UBadge>
        </template>
        <template #actions-data="{ row }">
          <div class="flex gap-2">
            <UButton variant="ghost" icon="i-heroicons-pencil" size="xs" @click="editUser(row)" />
            <UButton variant="ghost" icon="i-heroicons-trash" size="xs" color="red" @click="confirmDelete(row)" />
          </div>
        </template>
      </DataTable>
    </UCard>

    <!-- Add/Edit User Modal -->
    <UModal v-model="showModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">{{ editingUser ? 'Edit User' : 'Add New User' }}</h3>
        </template>
        
        <form class="space-y-4" @submit.prevent="saveUser">
          <UFormGroup label="Username" required hint="Unique login name" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.username" placeholder="e.g. john.smith" />
          </UFormGroup>
          <UFormGroup label="Email" required hint="Valid email address" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.email" type="email" placeholder="e.g. john@company.com" />
          </UFormGroup>
          <UFormGroup label="Role" required hint="User permission level" :ui="{ hint: 'text-xs text-gray-400' }">
            <USelect v-model="form.role" :options="roleOptions" placeholder="Select role" />
          </UFormGroup>
          <UFormGroup label="Password" :required="!editingUser" :hint="editingUser ? 'Leave blank to keep current' : 'Minimum 8 characters'" :ui="{ hint: 'text-xs text-gray-400' }">
            <UInput v-model="form.password" type="password" :placeholder="editingUser ? '••••••••' : 'Enter password'" />
          </UFormGroup>
        </form>
        
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showModal = false">Cancel</UButton>
            <UButton @click="saveUser" :loading="saving" :disabled="!form.username || !form.email || !form.role || (!editingUser && !form.password)">{{ editingUser ? 'Update' : 'Create' }}</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Delete Confirmation Modal -->
    <UModal v-model="showDeleteModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-red-600">Delete User</h3>
        </template>
        <p>Are you sure you want to delete <strong>{{ deletingUser?.username }}</strong>? This action cannot be undone.</p>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton variant="ghost" @click="showDeleteModal = false">Cancel</UButton>
            <UButton color="red" @click="deleteUser" :loading="deleting">Delete</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'default' })

const { $api } = useNuxtApp()
const toast = useToast()

// State
const users = ref<any[]>([])
const loading = ref(true)
const showModal = ref(false)
const showDeleteModal = ref(false)
const saving = ref(false)
const deleting = ref(false)
const editingUser = ref<any>(null)
const deletingUser = ref<any>(null)

const form = reactive({
  username: '',
  email: '',
  role: 'STAFF',
  password: ''
})

const roleOptions = [
  { label: 'Manager', value: 'MANAGER' },
  { label: 'Production', value: 'PRODUCTION' },
  { label: 'Warehouse', value: 'WAREHOUSE' },
  { label: 'Staff', value: 'STAFF' },
  { label: 'Procurement', value: 'PROCUREMENT' },
  { label: 'Finance', value: 'FINANCE' },
  { label: 'HR', value: 'HR' },
  { label: 'Lab Tech', value: 'LAB_TECH' }
]

const columns = [
  { key: 'username', label: 'Username' },
  { key: 'email', label: 'Email' },
  { key: 'role', label: 'Role' },
  { key: 'is_verified', label: 'Status' },
  { key: 'actions', label: '' }
]

const getRoleColor = (role: string) => {
  const colors: Record<string, string> = {
    ADMIN: 'red',
    MANAGER: 'purple',
    PRODUCTION: 'blue',
    WAREHOUSE: 'teal',
    STAFF: 'gray',
    PROCUREMENT: 'orange',
    FINANCE: 'green',
    HR: 'pink',
    LAB_TECH: 'cyan'
  }
  return colors[role] || 'gray'
}

// Fetch users
const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await $api.get('/users', { baseURL: '/api' })
    users.value = res.data || []
  } catch (e) {
    console.error('Failed to fetch users:', e)
    users.value = []
  } finally {
    loading.value = false
  }
}

// Open add user modal
const openAddUser = () => {
  editingUser.value = null
  form.username = ''
  form.email = ''
  form.role = 'STAFF'
  form.password = ''
  showModal.value = true
}

// Edit user
const editUser = (user: any) => {
  editingUser.value = user
  form.username = user.username
  form.email = user.email
  form.role = user.role
  form.password = ''
  showModal.value = true
}

// Save user
const saveUser = async () => {
  saving.value = true
  try {
    if (editingUser.value) {
      await $api.put(`/users/${editingUser.value.id}`, {
        username: form.username,
        email: form.email,
        role: form.role,
        ...(form.password && { password: form.password })
      }, { baseURL: '/api' })
      toast.add({ title: 'User updated successfully' })
    } else {
      await $api.post('/users', {
        username: form.username,
        email: form.email,
        role: form.role,
        password: form.password
      }, { baseURL: '/api' })
      toast.add({ title: 'User created successfully' })
    }
    showModal.value = false
    await fetchUsers()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to save user', color: 'red' })
  } finally {
    saving.value = false
  }
}

// Confirm delete
const confirmDelete = (user: any) => {
  deletingUser.value = user
  showDeleteModal.value = true
}

// Delete user
const deleteUser = async () => {
  if (!deletingUser.value) return
  deleting.value = true
  try {
    await $api.delete(`/users/${deletingUser.value.id}`, { baseURL: '/api' })
    toast.add({ title: 'User deleted successfully' })
    showDeleteModal.value = false
    await fetchUsers()
  } catch (e: any) {
    toast.add({ title: 'Error', description: e.response?.data?.detail || 'Failed to delete user', color: 'red' })
  } finally {
    deleting.value = false
  }
}

// Init
onMounted(() => {
  fetchUsers()
})
</script>
