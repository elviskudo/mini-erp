<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold text-gray-900">Chart of Accounts</h2>
      <UButton icon="i-heroicons-arrow-path" variant="ghost" @click="fetchAccounts">Refresh</UButton>
    </div>

    <UCard>
      <!-- Tree View Implementation using recursive component or simple list with indentation -->
      <div v-if="loading" class="text-center py-4">Loading accounts...</div>
      <div v-else class="space-y-1">
         <div v-for="node in flattenedAccounts" :key="node.id" 
              class="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded border-b border-gray-100"
              :style="{ marginLeft: `${node.level * 20}px` }">
            <span class="font-mono text-sm text-blue-600 font-bold w-24">{{ node.code }}</span>
            <span class="flex-1 font-medium text-gray-700">{{ node.name }}</span>
            <UBadge color="gray" variant="soft" size="xs">{{ node.type }}</UBadge>
         </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
const { $api } = useNuxtApp()
const loading = ref(false)
const accounts = ref([])
const flattenedAccounts = ref([])

const fetchAccounts = async () => {
    loading.value = true
    try {
        const res = await $api.get('/finance/coa')
        accounts.value = res.data
        flattenedAccounts.value = flattenTree(res.data)
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
}

// Helper to flatten tree for simple rendering with indentation
const flattenTree = (nodes: any[], level = 0): any[] => {
    let result: any[] = []
    for (const node of nodes) {
        result.push({ ...node, level })
        if (node.children && node.children.length > 0) {
            result = result.concat(flattenTree(node.children, level + 1))
        }
    }
    return result
}

onMounted(() => {
    fetchAccounts()
})
</script>
