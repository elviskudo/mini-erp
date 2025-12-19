<template>
  <div class="inline-block">
    <canvas ref="qrcodeRef"></canvas>
  </div>
</template>

<script setup lang="ts">
import QRCode from 'qrcode'

const props = defineProps<{
  value: string
  size?: number
}>()

const qrcodeRef = ref<HTMLCanvasElement | null>(null)

const generateQRCode = async () => {
  if (qrcodeRef.value && props.value) {
    try {
      await QRCode.toCanvas(qrcodeRef.value, props.value, {
        width: props.size || 100,
        margin: 1,
        color: {
          dark: '#000000',
          light: '#ffffff'
        }
      })
    } catch (e) {
      console.error('QR Code generation failed:', e)
    }
  }
}

watch(() => props.value, generateQRCode, { immediate: true })

onMounted(() => {
  nextTick(generateQRCode)
})
</script>
