<template>
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 text-orange-500 animate-spin" />
      <p class="mt-2 text-gray-500">Loading POS...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

// Redirect to POS
if (process.client) {
  navigateTo('/pos')
}
</script>
