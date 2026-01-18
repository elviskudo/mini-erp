import { defineStore } from 'pinia'

export interface PageComponent {
    id: string
    type: 'button' | 'text' | 'image' | 'video' | 'product' | 'container'
    content: any
    styles: Record<string, any>
    children?: PageComponent[] // For container nesting
}

export interface PageState {
    id: string | null
    title: string
    slug: string
    components: PageComponent[]
    selectedComponentId: string | null
}

export const usePageBuilderStore = defineStore('page-builder', {
    state: (): PageState => ({
        id: null,
        title: 'Untitled Page',
        slug: 'untitled-page',
        components: [],
        selectedComponentId: null
    }),

    getters: {
        selectedComponent: (state) => {
            if (!state.selectedComponentId) return null
            // Simple flat search for now (recursive if nesting added later)
            return state.components.find(c => c.id === state.selectedComponentId)
        }
    },

    actions: {
        addComponent(type: PageComponent['type']) {
            const newComponent: PageComponent = {
                id: crypto.randomUUID(),
                type,
                content: getDefaultContent(type),
                styles: getDefaultStyles(type)
            }
            this.components.push(newComponent)
            this.selectedComponentId = newComponent.id
        },

        selectComponent(id: string) {
            this.selectedComponentId = id
        },

        updateSelectedComponent(updates: Partial<PageComponent>) {
            if (!this.selectedComponentId) return
            const index = this.components.findIndex(c => c.id === this.selectedComponentId)
            if (index !== -1) {
                this.components[index] = { ...this.components[index], ...updates }
            }
        },

        removeComponent(id: string) {
            this.components = this.components.filter(c => c.id !== id)
            if (this.selectedComponentId === id) {
                this.selectedComponentId = null
            }
        },

        reorderComponents(newOrder: PageComponent[]) {
            this.components = newOrder
        }
    }
})

function getDefaultContent(type: string) {
    switch (type) {
        case 'button': return { text: 'Click Me', url: '#' }
        case 'text': return { text: 'Edit this text' }
        case 'image': return { src: 'https://placehold.co/600x400', alt: 'Placeholder' }
        case 'video': return { url: '' }
        case 'product': return { productId: null }
        default: return {}
    }
}

function getDefaultStyles(type: string) {
    return {
        marginTop: '0px',
        marginBottom: '16px',
        textAlign: 'left'
    }
}
