<template>
  <div class="min-h-screen bg-white">
    <div v-if="loading" class="flex justify-center items-center h-screen">
       <div class="animate-spin rounded-full h-12 w-12 border-4 border-pink-500 border-t-transparent"></div>
    </div>
    
    <div v-else class="max-w-4xl mx-auto px-4 py-8">
        <!-- Render Components -->
        <div v-for="comp in components" :key="comp.id" class="mb-4">
            <component :is="getComponentRenderer(comp.type)" :data="comp" />
        </div>
        
        <div v-if="components.length === 0" class="text-center py-20 text-gray-500">
            This page is empty.
        </div>
    </div>
    
    <!-- Branding Footer -->
    <div class="border-t border-gray-100 py-6 text-center text-xs text-gray-400">
        Powered by <span class="font-bold text-gray-600">NAIKIN</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePageBuilderStore } from '~/stores/page-builder'

definePageMeta({
  layout: 'blank'
})

const route = useRoute()
const store = usePageBuilderStore()
const loading = ref(true)
const components = ref<any[]>([])

onMounted(() => {
    // In a real app, fetch from API by username+slug
    // For now, if we came from builder, show store data.
    // Otherwise show mock data.
    
    const previewId = route.query.id as string
    
    setTimeout(() => {
        if (store.components.length > 0) {
            components.value = store.components
        } else if (previewId) {
            // Try loading from localStorage mock
            const saved = localStorage.getItem(`naikin_page_${previewId}`)
            if (saved) {
                const data = JSON.parse(saved)
                components.value = data.components
            }
        } 
        
        if (components.value.length === 0) {
             // Mock Data for demo
             components.value = [
                 { id: '1', type: 'text', content: { text: "Welcome to My Viral Campaign" }, styles: { fontSize: '2.5rem', fontWeight: 'bold', textAlign: 'center', marginBottom: '2rem' } },
                 { id: '2', type: 'image', content: { src: "https://placehold.co/800x400" }, styles: { marginBottom: '2rem' } },
                 { id: '3', type: 'text', content: { text: "This is a sub-headline describing the amazing offer." }, styles: { fontSize: '1.25rem', textAlign: 'center', color: '#666' } },
                 { id: '4', type: 'button', content: { text: "Buy Now - Only $99", url: '#' }, styles: { textAlign: 'center', marginTop: '2rem' } }
             ]
        }
        loading.value = false
    }, 500)
})


// Renderer Logic (Duplicated from Builder for now - should be shared composable)
const TextRenderer = defineComponent({
    props: ['data'],
    template: `<div :style="data.styles" class="prose prose-lg max-w-none mx-auto">{{ data.content.text }}</div>`
})

const ButtonRenderer = defineComponent({
    props: ['data'],
    template: `
        <div :style="data.styles">
            <a :href="'/naikin/checkout/mock-product-id'" class="inline-block px-8 py-4 bg-pink-600 text-white font-bold text-lg rounded-full hover:bg-pink-700 hover:shadow-lg transition transform hover:-translate-y-1">
                {{ data.content.text }}
            </a>
        </div>
    `
})

const ImageRenderer = defineComponent({
    props: ['data'],
    template: `
        <div :style="data.styles" class="flex justify-center">
            <img :src="data.content.src" class="max-w-full h-auto rounded-xl shadow-md" alt="img" />
        </div>
    `
})

const DefaultRenderer = defineComponent({ template: `<div></div>` })

const getComponentRenderer = (type: string) => {
    switch (type) {
        case 'text': return TextRenderer
        case 'button': return ButtonRenderer
        case 'image': return ImageRenderer
        default: return DefaultRenderer
    }
}
</script>
