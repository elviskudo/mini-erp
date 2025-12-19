<template>
  <div class="inline-block">
    <svg ref="barcodeRef"></svg>
  </div>
</template>

<script setup lang="ts">
import JsBarcode from 'jsbarcode'

const props = defineProps<{
  value: string
  width?: number
  height?: number
  displayValue?: boolean
}>()

const barcodeRef = ref<SVGElement | null>(null)

const generateBarcode = () => {
  if (barcodeRef.value && props.value) {
    try {
      JsBarcode(barcodeRef.value, props.value, {
        format: 'CODE128',
        width: props.width || 1.5,
        height: props.height || 40,
        displayValue: props.displayValue ?? true,
        fontSize: 12,
        margin: 5
      })
    } catch (e) {
      console.error('Barcode generation failed:', e)
    }
  }
}

watch(() => props.value, generateBarcode, { immediate: true })

onMounted(() => {
  nextTick(generateBarcode)
})
</script>
