<template>
  <USlideover v-model="modelValue" :ui="{ width: 'w-screen max-w-md' }">
    <div class="flex flex-col h-full">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b">
        <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
        <UButton 
          icon="i-heroicons-x-mark" 
          color="gray" 
          variant="ghost" 
          @click="close"
        />
      </div>
      
      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6">
        <slot />
      </div>
      
      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 px-6 py-4 border-t bg-gray-50">
        <UButton variant="ghost" @click="close">
          {{ cancelLabel }}
        </UButton>
        <UButton :loading="loading" @click="$emit('submit')">
          {{ submitLabel }}
        </UButton>
      </div>
    </div>
  </USlideover>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  modelValue: boolean
  title: string
  submitLabel?: string
  cancelLabel?: string
  loading?: boolean
}>(), {
  submitLabel: 'Save',
  cancelLabel: 'Cancel',
  loading: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'submit': []
}>()

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const close = () => {
  modelValue.value = false
}
</script>
