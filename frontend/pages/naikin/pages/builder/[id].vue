<template>
  <div class="h-screen flex flex-col bg-white overflow-hidden">
    <!-- Builder Header -->
    <header class="h-14 border-b border-gray-200 flex items-center justify-between px-4 bg-white z-10">
      <div class="flex items-center gap-4">
        <UButton icon="i-heroicons-arrow-left" color="gray" variant="ghost" to="/naikin/pages" />
        <div class="flex flex-col">
            <input 
                v-model="store.title" 
                class="font-bold text-gray-900 border-none p-0 focus:ring-0 text-sm h-5"
                placeholder="Page Title"
            />
            <span class="text-xs text-gray-400">/u/{{ store.slug }}</span>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <UButton color="white" icon="i-heroicons-computer-desktop" variant="ghost" />
        <UButton color="white" icon="i-heroicons-device-phone-mobile" variant="ghost" />
        <div class="h-6 w-px bg-gray-200 mx-2"></div>
        <UButton color="gray" variant="ghost">Save Draft</UButton>
        <UButton color="black" @click="publishPage">Publish</UButton>
      </div>
    </header>

    <!-- Main Workspace -->
    <div class="flex-1 flex overflow-hidden">
      
      <!-- Left Sidebar: Components -->
      <div class="w-64 border-r border-gray-200 bg-gray-50 flex flex-col">
        <div class="p-4 border-b border-gray-200">
            <h3 class="font-bold text-xs uppercase text-gray-400">Components</h3>
        </div>
        <div class="p-4 grid grid-cols-2 gap-3 overflow-y-auto">
             <div 
                v-for="comp in availableComponents" 
                :key="comp.type"
                class="bg-white border border-gray-200 rounded-lg p-3 flex flex-col items-center justify-center cursor-move hover:border-pink-500 hover:shadow-sm transition-all h-24"
                draggable="true"
                @dragstart="onDragStart($event, comp.type)"
                @click="store.addComponent(comp.type)"
             >
                <UIcon :name="comp.icon" class="w-6 h-6 text-gray-500 mb-2" />
                <span class="text-xs font-medium text-gray-700">{{ comp.label }}</span>
             </div>
        </div>
      </div>

      <!-- Center: Canvas -->
      <div class="flex-1 bg-gray-100 p-8 overflow-y-auto flex justify-center" @click.self="store.selectComponent(null)">
        <div class="w-full max-w-[800px] bg-white min-h-[calc(100vh-8rem)] shadow-lg rounded-none sm:rounded-md transition-all">
            <draggable 
                v-model="components" 
                item-key="id"
                class="min-h-[500px] p-8 space-y-2"
                group="components"
                ghost-class="ghost"
            >
                <template #item="{ element }">
                    <div 
                        class="relative group border-2 border-transparent hover:border-blue-200 transition-all p-2 rounded"
                        :class="{ 'border-blue-500 ring-2 ring-blue-500/20': store.selectedComponentId === element.id }"
                        @click.stop="store.selectComponent(element.id)"
                    >
                        <!-- Actions overlay -->
                        <div v-if="store.selectedComponentId === element.id" class="absolute -top-7 right-0 flex bg-blue-500 rounded-t text-white text-xs overflow-hidden z-10">
                            <button class="p-1.5 hover:bg-blue-600 block" @click.stop="store.removeComponent(element.id)">
                                <UIcon name="i-heroicons-trash" class="w-3 h-3" />
                            </button>
                            <button class="p-1.5 hover:bg-blue-600 cursor-move">
                                <UIcon name="i-heroicons-arrows-pointing-out" class="w-3 h-3" />
                            </button>
                        </div>

                        <!-- Component Rendering -->
                        <component :is="getComponentRenderer(element.type)" :data="element" />
                    </div>
                </template>
            </draggable>

            <div v-if="components.length === 0" class="h-[500px] flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-100 m-8 rounded-lg">
                <UIcon name="i-heroicons-cloud-arrow-down" class="w-12 h-12 mb-2" />
                <p>Drag components here</p>
            </div>
        </div>
      </div>

      <!-- Right Sidebar: Properties -->
      <div class="w-72 border-l border-gray-200 bg-white shadow-xl z-20" v-if="store.selectedComponent">
        <div class="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
            <h3 class="font-bold text-sm text-gray-900">Properties</h3>
            <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" size="xs" @click="store.selectComponent(null)" />
        </div>
        
        <div class="p-4 space-y-6 overflow-y-auto h-[calc(100vh-4rem)]">
            <!-- Text Content -->
            <div v-if="store.selectedComponent.type === 'text' || store.selectedComponent.type === 'button'" class="space-y-2">
                <label class="text-xs font-bold text-gray-500 uppercase">Text Content</label>
                <UTextarea v-if="store.selectedComponent.type === 'text'" v-model="store.selectedComponent.content.text" :rows="3" />
                <UInput v-else v-model="store.selectedComponent.content.text" />
            </div>

            <!-- URL -->
            <div v-if="store.selectedComponent.type === 'button' || store.selectedComponent.type === 'image'" class="space-y-2">
                <label class="text-xs font-bold text-gray-500 uppercase">{{ store.selectedComponent.type === 'image' ? 'Image Source URL' : 'Link URL' }}</label>
                <UInput v-if="store.selectedComponent.type === 'button'" v-model="store.selectedComponent.content.url" placeholder="https://..." icon="i-heroicons-link" />
                 <UInput v-else v-model="store.selectedComponent.content.src" placeholder="https://..." icon="i-heroicons-photo" />
            </div>

            <!-- Styles -->
             <div class="space-y-4 pt-4 border-t border-gray-100">
                <label class="text-xs font-bold text-gray-500 uppercase">Styles</label>
                
                <div class="grid grid-cols-2 gap-2">
                    <div class="flex flex-col gap-1">
                        <span class="text-xs text-gray-400">Align</span>
                         <USelectMenu v-model="store.selectedComponent.styles.textAlign" :options="['left', 'center', 'right']" size="xs" />
                    </div>
                     <div class="flex flex-col gap-1">
                        <span class="text-xs text-gray-400">Margin Bot</span>
                        <UInput v-model="store.selectedComponent.styles.marginBottom" size="xs" />
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import draggable from 'vuedraggable'
import { usePageBuilderStore } from '~/stores/page-builder'

definePageMeta({
  layout: 'blank',
  middleware: 'auth'
})

const store = usePageBuilderStore()

// Two-way binding for draggable
const components = computed({
    get: () => store.components,
    set: (val) => store.reorderComponents(val)
})

const availableComponents = [
    { type: 'text', icon: 'i-heroicons-bars-3-bottom-left', label: 'Text Block' },
    { type: 'button', icon: 'i-heroicons-cursor-arrow-rays', label: 'Button' },
    { type: 'image', icon: 'i-heroicons-photo', label: 'Image' },
    { type: 'video', icon: 'i-heroicons-video-camera', label: 'Video' },
    { type: 'product', icon: 'i-heroicons-shopping-bag', label: 'Product Card' },
    { type: 'container', icon: 'i-heroicons-square-3-stack-3d', label: 'Container' },
]

const onDragStart = (evt: DragEvent, type: string) => {
    // Basic drag start logic if we wanted native dnd, but vuedraggable handles lists
    // We actually need a second list for "source" to drag FROM if we want DnD from sidebar
    // Or just click to add for simplicity MVP
}

// Simple Renderer Components (inline for now)
const TextRenderer = defineComponent({
    props: ['data'],
    template: `<div :style="data.styles" class="prose prose-sm max-w-none">{{ data.content.text }}</div>`
})

const ButtonRenderer = defineComponent({
    props: ['data'],
    template: `
        <div :style="data.styles">
            <a href="#" class="inline-block px-6 py-3 bg-pink-600 text-white font-bold rounded-lg hover:bg-pink-700 transition">
                {{ data.content.text }}
            </a>
        </div>
    `
})

const ImageRenderer = defineComponent({
    props: ['data'],
    template: `
        <div :style="data.styles">
            <img :src="data.content.src" class="w-full h-auto rounded-lg" alt="img" />
        </div>
    `
})

const DefaultRenderer = defineComponent({ template: `<div class="p-4 border border-dashed text-gray-400">Unknown Component</div>` })

// Mock Publish Logic
const publishPage = () => {
    // Save to localStorage to simulate DB
    const pageData = {
        title: store.title,
        slug: store.slug,
        components: store.components
    }
    localStorage.setItem(`naikin_page_${store.id}`, JSON.stringify(pageData))
    
    // Open public URL
    // Assuming current user is "elviskudo" (or any username)
    // In real app, we'd get username from authStore
    const url = `/u/elviskudo/${store.slug}?preview=true&id=${store.id}`
    window.open(url, '_blank')
}
</script>

<style scoped>
.ghost {
    opacity: 0.5;
    background: #eff6ff;
    border: 2px dashed #3b82f6;
}
</style>
