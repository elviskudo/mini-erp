<template>
  <div class="animate-pulse">
    <!-- Table Skeleton -->
    <div v-if="type === 'table'" class="space-y-3">
      <div v-for="i in rows" :key="i" class="flex items-center gap-4">
        <div v-for="j in columns" :key="j" class="flex-1">
          <div class="h-4 bg-gray-200 rounded" :class="getRandomWidth()"></div>
        </div>
      </div>
    </div>

    <!-- Cards Skeleton -->
    <div v-else-if="type === 'cards'" class="grid gap-4" :class="gridClass">
      <div v-for="i in count" :key="i" class="p-4 bg-white rounded-lg border">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 bg-gray-200 rounded-lg"></div>
          <div class="flex-1 space-y-2">
            <div class="h-5 bg-gray-200 rounded w-16"></div>
            <div class="h-3 bg-gray-100 rounded w-24"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- List Skeleton -->
    <div v-else-if="type === 'list'" class="space-y-3">
      <div v-for="i in rows" :key="i" class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
        <div class="w-10 h-10 bg-gray-200 rounded-full"></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 bg-gray-200 rounded w-1/3"></div>
          <div class="h-3 bg-gray-100 rounded w-1/2"></div>
        </div>
        <div class="w-20 h-6 bg-gray-200 rounded"></div>
      </div>
    </div>

    <!-- Single Line -->
    <div v-else-if="type === 'line'" class="space-y-2">
      <div v-for="i in rows" :key="i" class="h-4 bg-gray-200 rounded" :class="getRandomWidth()"></div>
    </div>

    <!-- Chart Skeleton -->
    <div v-else-if="type === 'chart'" class="h-64 flex items-end gap-2 p-4">
      <div v-for="i in 7" :key="i" class="flex-1 bg-gray-200 rounded-t" :style="{ height: `${20 + Math.random() * 60}%` }"></div>
    </div>

    <!-- Circle Stats Skeleton -->
    <div v-else-if="type === 'circles'" class="flex justify-around">
      <div v-for="i in count" :key="i" class="text-center">
        <div class="w-24 h-24 bg-gray-200 rounded-full mx-auto mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-20 mx-auto"></div>
      </div>
    </div>

    <!-- Default Block -->
    <div v-else class="space-y-3">
      <div class="h-4 bg-gray-200 rounded w-3/4"></div>
      <div class="h-4 bg-gray-200 rounded w-1/2"></div>
      <div class="h-4 bg-gray-200 rounded w-5/6"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  type?: 'table' | 'cards' | 'list' | 'line' | 'chart' | 'circles' | 'block'
  rows?: number
  columns?: number
  count?: number
  gridCols?: number
}

const props = withDefaults(defineProps<Props>(), {
  type: 'block',
  rows: 5,
  columns: 4,
  count: 4,
  gridCols: 4
})

const gridClass = computed(() => {
  const gridMap: Record<number, string> = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-2 md:grid-cols-4'
  }
  return gridMap[props.gridCols] || 'grid-cols-4'
})

const widths = ['w-full', 'w-3/4', 'w-1/2', 'w-2/3', 'w-5/6']
const getRandomWidth = () => widths[Math.floor(Math.random() * widths.length)]
</script>

<style scoped>
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-pulse > div > div {
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
</style>
