<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Create New Landing Page
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        Start building your high-converting page
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <form class="space-y-6" @submit.prevent="handleCreate">
          <div>
            <label for="title" class="block text-sm font-medium text-gray-700">Page Title</label>
            <div class="mt-1">
              <input id="title" v-model="form.title" type="text" required class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-pink-500 focus:border-pink-500 sm:text-sm" placeholder="e.g. Viral Ebook Campaign" />
            </div>
          </div>

          <div>
            <label for="slug" class="block text-sm font-medium text-gray-700">URL Slug</label>
            <div class="mt-1 flex rounded-md shadow-sm">
              <span class="inline-flex items-center px-3 rounded-l-md border border-r-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                naikin/u/
              </span>
              <input id="slug" v-model="form.slug" type="text" class="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-r-md focus:ring-pink-500 focus:border-pink-500 sm:text-sm border-gray-300" placeholder="my-campaign" />
            </div>
          </div>

          <div>
            <button type="submit" :disabled="loading" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-pink-600 hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500">
              <span v-if="loading">Creating...</span>
              <span v-else>Start Building</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePageBuilderStore } from '~/stores/page-builder'

definePageMeta({
  layout: 'blank',
  middleware: 'auth'
})

const router = useRouter()
const store = usePageBuilderStore()

const form = reactive({
  title: '',
  slug: ''
})

const loading = ref(false)

// Auto-generate slug from title
watch(() => form.title, (newVal) => {
  if (!form.slug || form.slug === toSlug(oldVal)) {
     form.slug = toSlug(newVal)
  }
})

let oldVal = ''
watch(() => form.title, (val) => { oldVal = val })

function toSlug(text: string) {
    return text
        .toLowerCase()
        .replace(/[^\w ]+/g, '')
        .replace(/ +/g, '-')
}

const handleCreate = async () => {
  loading.value = true
  // Mock API call simulation
  setTimeout(() => {
    // Reset store
    store.id = crypto.randomUUID()
    store.title = form.title
    store.slug = form.slug
    store.components = []
    store.selectedComponentId = null

    loading.value = false
    router.push(`/naikin/pages/builder/${store.id}`)
  }, 800)
}
</script>
