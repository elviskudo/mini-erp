<template>
  <div class="h-screen flex flex-col bg-gray-100">
    <!-- Top Bar -->
    <div class="bg-white border-b px-4 py-2 flex items-center gap-4 shrink-0">
      <UButton icon="i-heroicons-arrow-left" color="gray" variant="ghost" @click="goBack" />
      <div class="flex-1">
        <UInput v-model="pageData.title" placeholder="Page Title" class="max-w-xs" @input="markDirty" />
      </div>
      <UBadge :color="isDirty ? 'yellow' : 'green'" variant="subtle">{{ isDirty ? 'Unsaved' : 'Saved' }}</UBadge>
      <UButton variant="outline" @click="savePage">Save</UButton>
      <UButton variant="outline" color="blue" @click="showPreview = true">Preview</UButton>
      <UButton @click="publishPage">Publish</UButton>
    </div>

    <div class="flex flex-1 overflow-hidden">
      <!-- Left Sidebar - Components -->
      <div class="w-56 bg-white border-r p-3 overflow-y-auto shrink-0">
        <h3 class="text-xs font-semibold text-gray-500 mb-2 uppercase">Components</h3>
        <div class="space-y-1.5">
          <div
            v-for="comp in componentTypes"
            :key="comp.type"
            draggable="true"
            @dragstart="onDragStart($event, comp.type)"
            class="flex items-center gap-2 p-2 bg-gray-50 rounded cursor-move hover:bg-gray-100 border text-sm"
          >
            <UIcon :name="comp.icon" class="text-gray-500" />
            <span>{{ comp.label }}</span>
          </div>
        </div>
      </div>

      <!-- Canvas -->
      <div 
        class="flex-1 p-6 overflow-y-auto"
        @dragover.prevent
        @drop="onDropCanvas"
      >
        <div class="mx-auto max-w-3xl min-h-full bg-white rounded-lg shadow-lg p-6">
          <div v-if="pageData.elements.length === 0" class="text-center py-20 text-gray-400">
            <UIcon name="i-heroicons-square-3-stack-3d" class="text-5xl mb-3" />
            <p>Drag components here</p>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="(el, idx) in pageData.elements"
              :key="el.id"
              class="relative group border-2 rounded p-2 transition-colors"
              :class="selectedId === el.id ? 'border-blue-500 bg-blue-50' : 'border-transparent hover:border-gray-300'"
              @click="selectElement(el.id)"
            >
              <!-- Element Controls - Always visible when selected, show on hover otherwise -->
              <div 
                class="absolute -top-8 right-0 flex gap-0.5 bg-white shadow-md rounded-lg border px-1.5 py-1 z-10 transition-opacity"
                :class="selectedId === el.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'"
              >
                <UButton icon="i-heroicons-arrow-up" size="xs" color="gray" variant="ghost" @click.stop="moveEl(idx, -1)" :disabled="idx === 0" title="Move Up" />
                <UButton icon="i-heroicons-arrow-down" size="xs" color="gray" variant="ghost" @click.stop="moveEl(idx, 1)" :disabled="idx === pageData.elements.length - 1" title="Move Down" />
                <UButton icon="i-heroicons-document-duplicate" size="xs" color="blue" variant="ghost" @click.stop="duplicateEl(idx)" title="Duplicate" />
                <UButton icon="i-heroicons-trash" size="xs" color="red" variant="ghost" @click.stop="removeEl(idx)" title="Delete" />
              </div>

              <!-- Text -->
              <p v-if="el.type === 'text'" :class="[el.fontSize, el.fontWeight, el.textAlign]">{{ el.content }}</p>

              <!-- Image -->
              <img v-else-if="el.type === 'image'" :src="el.src" :alt="el.alt" :class="[el.width, 'rounded']" />

              <!-- Video -->
              <div v-else-if="el.type === 'video'" class="aspect-video">
                <iframe :src="el.src" class="w-full h-full rounded" frameborder="0" allowfullscreen></iframe>
              </div>

              <!-- Button -->
              <div v-else-if="el.type === 'button'" class="py-2">
                <span :class="['inline-block px-5 py-2 rounded font-medium text-white', getBtnClass(el.color)]">{{ el.text }}</span>
              </div>

              <!-- Card -->
              <div v-else-if="el.type === 'card'" class="border rounded-lg overflow-hidden">
                <img v-if="el.image" :src="el.image" class="w-full h-40 object-cover" />
                <div class="p-3">
                  <h4 class="font-semibold">{{ el.title }}</h4>
                  <p class="text-sm text-gray-600 mt-1">{{ el.description }}</p>
                </div>
              </div>

              <!-- Hero -->
              <div v-else-if="el.type === 'hero'" :class="[el.bgColor, el.padding, 'rounded-lg text-center']" :style="{ color: el.textColor || '#fff' }">
                <h1 class="text-3xl font-bold mb-2">{{ el.heading || 'Heading' }}</h1>
                <p class="text-lg opacity-90">{{ el.subheading || 'Subheading' }}</p>
              </div>

              <!-- Divider -->
              <hr v-else-if="el.type === 'divider'" :class="[el.style, 'border-gray-300']" />

              <!-- Spacer -->
              <div v-else-if="el.type === 'spacer'" :class="el.height"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Sidebar - Properties -->
      <div class="w-64 bg-white border-l p-4 overflow-y-auto shrink-0">
        <template v-if="selectedElement">
          <h3 class="text-xs font-semibold text-gray-500 mb-3 uppercase">Properties</h3>

          <!-- Text Properties -->
          <div v-if="selectedElement.type === 'text'" class="space-y-3">
            <UFormGroup label="Content">
              <UTextarea v-model="selectedElement.content" rows="4" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Size">
              <USelectMenu v-model="selectedElement.fontSize" :options="fontSizes" @change="markDirty" />
            </UFormGroup>
            <UFormGroup label="Weight">
              <USelectMenu v-model="selectedElement.fontWeight" :options="fontWeights" @change="markDirty" />
            </UFormGroup>
            <UFormGroup label="Align">
              <USelectMenu v-model="selectedElement.textAlign" :options="textAligns" @change="markDirty" />
            </UFormGroup>
          </div>

          <!-- Image Properties -->
          <div v-else-if="selectedElement.type === 'image'" class="space-y-3">
            <UFormGroup label="Image URL">
              <UInput v-model="selectedElement.src" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Alt Text">
              <UInput v-model="selectedElement.alt" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Width">
              <USelectMenu v-model="selectedElement.width" :options="widths" @change="markDirty" />
            </UFormGroup>
          </div>

          <!-- Video Properties -->
          <div v-else-if="selectedElement.type === 'video'" class="space-y-3">
            <UFormGroup label="Video URL">
              <UInput v-model="selectedElement.src" placeholder="YouTube embed URL" @input="markDirty" />
            </UFormGroup>
          </div>

          <!-- Button Properties -->
          <div v-else-if="selectedElement.type === 'button'" class="space-y-3">
            <UFormGroup label="Button Text">
              <UInput v-model="selectedElement.text" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Link URL">
              <UInput v-model="selectedElement.href" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Color">
              <USelectMenu v-model="selectedElement.color" :options="btnColors" @change="markDirty" />
            </UFormGroup>
          </div>

          <!-- Card Properties -->
          <div v-else-if="selectedElement.type === 'card'" class="space-y-3">
            <UFormGroup label="Title">
              <UInput v-model="selectedElement.title" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Description">
              <UTextarea v-model="selectedElement.description" rows="3" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Image URL">
              <UInput v-model="selectedElement.image" @input="markDirty" />
            </UFormGroup>
          </div>

          <!-- Hero Properties -->
          <div v-else-if="selectedElement.type === 'hero'" class="space-y-3">
            <UFormGroup label="Heading">
              <UInput v-model="selectedElement.heading" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Subheading">
              <UInput v-model="selectedElement.subheading" @input="markDirty" />
            </UFormGroup>
            <UFormGroup label="Background">
              <USelectMenu v-model="selectedElement.bgColor" :options="bgColors" @change="markDirty" />
            </UFormGroup>
            <UFormGroup label="Padding">
              <USelectMenu v-model="selectedElement.padding" :options="paddings" @change="markDirty" />
            </UFormGroup>
          </div>

          <!-- Divider Properties -->
          <div v-else-if="selectedElement.type === 'divider'" class="space-y-3">
            <UFormGroup label="Style">
              <USelectMenu v-model="selectedElement.style" :options="['border-t', 'border-t-2', 'border-dashed border-t']" @change="markDirty" />
            </UFormGroup>
          </div>

          <!-- Spacer Properties -->
          <div v-else-if="selectedElement.type === 'spacer'" class="space-y-3">
            <UFormGroup label="Height">
              <USelectMenu v-model="selectedElement.height" :options="['h-4', 'h-8', 'h-12', 'h-16', 'h-24']" @change="markDirty" />
            </UFormGroup>
          </div>
        </template>
        <div v-else class="text-gray-400 text-center py-8 text-sm">
          Select an element to edit
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <UModal v-model="showPreview" fullscreen>
      <div class="h-full bg-white overflow-y-auto">
        <div class="sticky top-0 bg-white border-b p-3 flex justify-between items-center z-10">
          <span class="font-semibold">Preview: {{ pageData.title }}</span>
          <UButton icon="i-heroicons-x-mark" color="gray" variant="ghost" @click="showPreview = false" />
        </div>
        <div class="max-w-4xl mx-auto py-8 px-4">
          <template v-for="el in pageData.elements" :key="el.id">
            <p v-if="el.type === 'text'" :class="[el.fontSize, el.fontWeight, el.textAlign, 'mb-4']">{{ el.content }}</p>
            <img v-else-if="el.type === 'image'" :src="el.src" :alt="el.alt" :class="[el.width, 'rounded mb-4']" />
            <div v-else-if="el.type === 'video'" class="aspect-video mb-4"><iframe :src="el.src" class="w-full h-full rounded" frameborder="0" allowfullscreen></iframe></div>
            <div v-else-if="el.type === 'button'" class="mb-4"><a :href="el.href" :class="['inline-block px-6 py-3 rounded-lg font-medium text-white', getBtnClass(el.color)]">{{ el.text }}</a></div>
            <div v-else-if="el.type === 'card'" class="border rounded-lg overflow-hidden shadow mb-4"><img v-if="el.image" :src="el.image" class="w-full h-48 object-cover" /><div class="p-4"><h3 class="font-semibold text-lg">{{ el.title }}</h3><p class="text-gray-600 mt-1">{{ el.description }}</p></div></div>
            <div v-else-if="el.type === 'hero'" :class="[el.bgColor, el.padding, 'rounded-lg text-center mb-4']" :style="{ color: el.textColor || '#fff' }"><h1 class="text-4xl font-bold mb-3">{{ el.heading }}</h1><p class="text-xl opacity-90">{{ el.subheading }}</p></div>
            <hr v-else-if="el.type === 'divider'" :class="[el.style, 'border-gray-300 my-4']" />
            <div v-else-if="el.type === 'spacer'" :class="el.height"></div>
          </template>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const toast = useToast()

definePageMeta({ layout: 'blank', middleware: 'auth' })

const pageId = computed(() => route.params.id as string)
const isDirty = ref(false)
const showPreview = ref(false)
const selectedId = ref<string | null>(null)

const pageData = reactive({
    id: '',
    title: 'Untitled Page',
    slug: '',
    status: 'draft',
    elements: [] as any[],
    updated_at: ''
})

const componentTypes = [
    { type: 'text', label: 'Text', icon: 'i-heroicons-bars-3-bottom-left' },
    { type: 'image', label: 'Image', icon: 'i-heroicons-photo' },
    { type: 'video', label: 'Video', icon: 'i-heroicons-play-circle' },
    { type: 'button', label: 'Button', icon: 'i-heroicons-cursor-arrow-rays' },
    { type: 'card', label: 'Card', icon: 'i-heroicons-rectangle-group' },
    { type: 'hero', label: 'Hero', icon: 'i-heroicons-sparkles' },
    { type: 'divider', label: 'Divider', icon: 'i-heroicons-minus' },
    { type: 'spacer', label: 'Spacer', icon: 'i-heroicons-arrows-up-down' }
]

const fontSizes = ['text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl']
const fontWeights = ['font-normal', 'font-medium', 'font-semibold', 'font-bold']
const textAligns = ['text-left', 'text-center', 'text-right']
const widths = ['w-full', 'w-3/4', 'w-1/2', 'w-1/3']
const btnColors = ['primary', 'green', 'red', 'orange', 'gray']
const bgColors = ['bg-gray-100', 'bg-blue-600', 'bg-green-600', 'bg-purple-600', 'bg-gradient-to-r from-blue-600 to-purple-600']
const paddings = ['p-6', 'p-8', 'p-12', 'p-16', 'p-20']

const selectedElement = computed(() => pageData.elements.find(e => e.id === selectedId.value))

const getBtnClass = (color: string) => {
    const map: Record<string, string> = { primary: 'bg-blue-600', green: 'bg-green-600', red: 'bg-red-600', orange: 'bg-orange-500', gray: 'bg-gray-600' }
    return map[color] || 'bg-blue-600'
}

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2, 5)

const goBack = () => {
    if (isDirty.value && !confirm('Unsaved changes. Leave anyway?')) return
    router.push('/crm/marketing/pages')
}

const markDirty = () => { isDirty.value = true }

const onDragStart = (e: DragEvent, type: string) => {
    e.dataTransfer?.setData('type', type)
}

const onDropCanvas = (e: DragEvent) => {
    const type = e.dataTransfer?.getData('type')
    if (type) addElement(type)
}

const addElement = (type: string) => {
    const id = generateId()
    let el: any = { id, type }

    switch (type) {
        case 'text': el = { ...el, content: 'Edit this text...', fontSize: 'text-base', fontWeight: 'font-normal', textAlign: 'text-left' }; break
        case 'image': el = { ...el, src: 'https://placehold.co/800x400', alt: '', width: 'w-full' }; break
        case 'video': el = { ...el, src: 'https://www.youtube.com/embed/dQw4w9WgXcQ' }; break
        case 'button': el = { ...el, text: 'Click Me', href: '#', color: 'primary' }; break
        case 'card': el = { ...el, title: 'Card Title', description: 'Description here...', image: 'https://placehold.co/400x200' }; break
        case 'hero': el = { ...el, heading: 'Hero Heading', subheading: 'Subheading text', bgColor: 'bg-gradient-to-r from-blue-600 to-purple-600', padding: 'p-12' }; break
        case 'divider': el = { ...el, style: 'border-t' }; break
        case 'spacer': el = { ...el, height: 'h-8' }; break
    }

    pageData.elements.push(el)
    selectedId.value = id
    markDirty()
}

const selectElement = (id: string) => { selectedId.value = id }
const removeEl = (idx: number) => { pageData.elements.splice(idx, 1); selectedId.value = null; markDirty() }
const moveEl = (idx: number, dir: number) => {
    const newIdx = idx + dir
    if (newIdx < 0 || newIdx >= pageData.elements.length) return
    [pageData.elements[idx], pageData.elements[newIdx]] = [pageData.elements[newIdx], pageData.elements[idx]]
    markDirty()
}
const duplicateEl = (idx: number) => {
    const copy = { ...pageData.elements[idx], id: generateId() }
    pageData.elements.splice(idx + 1, 0, copy)
    markDirty()
}

const savePage = () => {
    pageData.id = pageId.value
    pageData.slug = pageData.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')
    pageData.updated_at = new Date().toISOString()

    const stored = localStorage.getItem('pageBuilder_pages')
    let pages = stored ? JSON.parse(stored) : []
    const existingIdx = pages.findIndex((p: any) => p.id === pageData.id)
    if (existingIdx >= 0) pages[existingIdx] = { ...pageData }
    else pages.push({ ...pageData })
    localStorage.setItem('pageBuilder_pages', JSON.stringify(pages))

    isDirty.value = false
    toast.add({ title: 'Saved', description: 'Page saved' })
}

const publishPage = () => {
    pageData.status = 'published'
    savePage()
    toast.add({ title: 'Published', description: 'Page is now live' })
}

onMounted(() => {
    const stored = localStorage.getItem('pageBuilder_pages')
    if (stored) {
        const pages = JSON.parse(stored)
        const existing = pages.find((p: any) => p.id === pageId.value)
        if (existing) {
            Object.assign(pageData, existing)
        }
    }
    pageData.id = pageId.value
})
</script>
