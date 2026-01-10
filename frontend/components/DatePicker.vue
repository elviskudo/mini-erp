<template>
  <div>
    <label v-if="label" class="block text-xs font-medium text-gray-700 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <div class="relative">
      <input
        ref="flatpickrInput"
        type="text"
        :placeholder="placeholder"
        :value="displayValue"
        readonly
        class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white cursor-pointer"
        :class="{ 'border-red-500': error }"
      />
      <UIcon name="i-heroicons-calendar" class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
    <p v-if="error" class="mt-1 text-xs text-red-500">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import flatpickr from 'flatpickr'
import 'flatpickr/dist/flatpickr.min.css'

const props = withDefaults(defineProps<{
  modelValue: string | string[]
  label?: string
  placeholder?: string
  mode?: 'single' | 'range'
  required?: boolean
  error?: string
}>(), {
  placeholder: 'Select date',
  mode: 'single',
  required: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
}>()

const flatpickrInput = ref<HTMLInputElement | null>(null)
let fp: flatpickr.Instance | null = null

const displayValue = computed(() => {
  if (!props.modelValue) return ''
  if (Array.isArray(props.modelValue)) {
    return props.modelValue.join(' to ')
  }
  return props.modelValue
})

onMounted(() => {
  if (flatpickrInput.value) {
    fp = flatpickr(flatpickrInput.value, {
      mode: props.mode,
      dateFormat: 'Y-m-d',
      defaultDate: props.modelValue,
      onChange: (selectedDates, dateStr) => {
        if (props.mode === 'range' && selectedDates.length === 2) {
          emit('update:modelValue', [
            selectedDates[0].toISOString().split('T')[0],
            selectedDates[1].toISOString().split('T')[0]
          ])
        } else if (props.mode === 'single' && selectedDates.length === 1) {
          emit('update:modelValue', selectedDates[0].toISOString().split('T')[0])
        }
      }
    })
  }
})

onUnmounted(() => {
  if (fp) fp.destroy()
})

watch(() => props.modelValue, (val) => {
  if (fp && val) {
    fp.setDate(val, false)
  }
})
</script>
