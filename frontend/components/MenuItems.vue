<template>
  <template v-for="(link, index) in items" :key="link.label">
    <!-- Direct Link (no children) -->
    <NuxtLink 
      v-if="!link.children || link.children.length === 0"
      :to="link.to"
      class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
      :class="[
        isActive(link.to) 
          ? 'bg-primary-50 text-primary-700' 
          : 'text-gray-700 hover:bg-gray-100'
      ]"
      @click="$emit('itemClick')"
    >
      <UIcon v-if="link.icon" :name="link.icon" class="w-5 h-5 flex-shrink-0" />
      <span>{{ link.label }}</span>
    </NuxtLink>
    
    <!-- Menu with Children (Popup) -->
    <div 
      v-else 
      :ref="el => setMenuRef(link.label, el)"
      class="relative"
      @mouseenter="handleMouseEnter(link.label, $event)"
      @mouseleave="handleMouseLeave"
    >
      <button 
        @click="toggleMenu(link.label, $event)"
        class="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="[
          isMenuOpen(link.label) || isChildActive(link.children)
            ? 'bg-primary-50 text-primary-700' 
            : 'text-gray-700 hover:bg-gray-100'
        ]"
      >
        <div class="flex items-center gap-3">
          <UIcon v-if="link.icon" :name="link.icon" class="w-5 h-5 flex-shrink-0" />
          <span>{{ link.label }}</span>
        </div>
        <UIcon 
          name="i-heroicons-chevron-right" 
          class="w-4 h-4 flex-shrink-0 transition-transform" 
        />
      </button>
      
      <!-- Popup Panel - appears to the right of the button -->
      <Teleport to="body">
        <Transition
          enter-active-class="transition ease-out duration-100"
          enter-from-class="transform opacity-0 scale-95"
          enter-to-class="transform opacity-100 scale-100"
          leave-active-class="transition ease-in duration-75"
          leave-from-class="transform opacity-100 scale-100"
          leave-to-class="transform opacity-0 scale-95"
        >
          <div 
            v-show="isMenuOpen(link.label)"
            class="fixed w-56 bg-white border border-gray-200 rounded-lg shadow-xl py-2"
            :style="getPopupStyle(link.label)"
            @mouseenter="handleMouseEnter(link.label, $event)"
            @mouseleave="handleMouseLeave"
          >
            <!-- Arrow pointer -->
            <div class="absolute -left-2 top-3 w-2 h-2 bg-white border-l border-b border-gray-200 rotate-45"></div>
            
            <!-- Recursive children -->
            <template v-for="child in link.children" :key="child.label">
              <!-- Child with sub-children -->
              <div 
                v-if="child.children && child.children.length > 0"
                :ref="el => setChildMenuRef(child.label, el)"
                class="relative"
                @mouseenter="handleChildMouseEnter(child.label, $event)"
                @mouseleave="handleChildMouseLeave"
              >
                <button 
                  class="w-full flex items-center justify-between px-4 py-2 text-sm transition-colors rounded-md hover:bg-gray-100"
                  :class="[
                    isChildMenuOpen(child.label) || isChildActive(child.children)
                      ? 'bg-primary-50 text-primary-700' 
                      : 'text-gray-600 hover:text-gray-900'
                  ]"
                >
                  <span>{{ child.label }}</span>
                  <UIcon name="i-heroicons-chevron-right" class="w-3 h-3" />
                </button>
                
                <!-- Sub-popup for nested children -->
                <div 
                  v-show="isChildMenuOpen(child.label)"
                  class="fixed w-48 bg-white border border-gray-200 rounded-lg shadow-xl py-2"
                  :style="getChildPopupStyle(child.label)"
                  @mouseenter="handleChildMouseEnter(child.label, $event)"
                  @mouseleave="handleChildMouseLeave"
                >
                  <!-- Arrow pointer -->
                  <div class="absolute -left-2 top-3 w-2 h-2 bg-white border-l border-b border-gray-200 rotate-45"></div>
                  
                  <NuxtLink 
                    v-for="subChild in child.children" 
                    :key="subChild.to"
                    :to="subChild.to"
                    class="block px-4 py-2 text-sm transition-colors rounded-md hover:bg-gray-100"
                    :class="[
                      isActive(subChild.to) 
                        ? 'bg-primary-50 text-primary-700 font-medium' 
                        : 'text-gray-600 hover:text-gray-900'
                    ]"
                    @click="handleItemClick"
                  >
                    {{ subChild.label }}
                  </NuxtLink>
                </div>
              </div>
              
              <!-- Simple child link -->
              <NuxtLink 
                v-else
                :to="child.to"
                class="block px-4 py-2 text-sm transition-colors rounded-md hover:bg-gray-100"
                :class="[
                  isActive(child.to) 
                    ? 'bg-primary-50 text-primary-700 font-medium' 
                    : 'text-gray-600 hover:text-gray-900'
                ]"
                @click="handleItemClick"
              >
                {{ child.label }}
              </NuxtLink>
            </template>
          </div>
        </Transition>
      </Teleport>
    </div>
  </template>
</template>

<script setup lang="ts">
interface MenuItem {
  label: string
  icon?: string
  to?: string
  children?: MenuItem[]
}

const props = defineProps<{
  items: MenuItem[]
}>()

const emit = defineEmits(['itemClick'])

const route = useRoute()
const openMenu = ref<string | null>(null)
const openChildMenu = ref<string | null>(null)

// Store references to menu elements for position calculation
const menuRefs = ref<Record<string, HTMLElement | null>>({})
const childMenuRefs = ref<Record<string, HTMLElement | null>>({})
const menuPositions = ref<Record<string, { top: number; left: number }>>({})
const childMenuPositions = ref<Record<string, { top: number; left: number }>>({})

let closeTimeout: ReturnType<typeof setTimeout> | null = null
let closeChildTimeout: ReturnType<typeof setTimeout> | null = null

const setMenuRef = (label: string, el: any) => {
  if (el) {
    menuRefs.value[label] = el as HTMLElement
  }
}

const setChildMenuRef = (label: string, el: any) => {
  if (el) {
    childMenuRefs.value[label] = el as HTMLElement
  }
}

const isActive = (path?: string) => {
  if (!path) return false
  return route.path === path
}

const isMenuOpen = (label: string) => {
  return openMenu.value === label
}

const isChildMenuOpen = (label: string) => {
  return openChildMenu.value === label
}

const isChildActive = (children?: MenuItem[]): boolean => {
  if (!children) return false
  return children.some(child => {
    if (isActive(child.to)) return true
    if (child.children) return isChildActive(child.children)
    return false
  })
}

const getPopupStyle = (label: string) => {
  const pos = menuPositions.value[label]
  if (pos) {
    return {
      top: `${pos.top}px`,
      left: `${pos.left}px`,
      zIndex: 10000
    }
  }
  return { top: '0px', left: '264px', zIndex: 10000 }
}

const getChildPopupStyle = (label: string) => {
  const pos = childMenuPositions.value[label]
  if (pos) {
    return {
      top: `${pos.top}px`,
      left: `${pos.left}px`,
      zIndex: 10001
    }
  }
  return { top: '0px', left: '0px', zIndex: 10001 }
}

const calculatePosition = (el: HTMLElement, menuLabel?: string) => {
  const rect = el.getBoundingClientRect()
  const viewportHeight = window.innerHeight
  
  // Estimate menu height based on children count (roughly 40px per item + padding)
  // Find the menu item to get children count
  let estimatedMenuHeight = 200 // default estimate
  if (menuLabel) {
    const menuItem = props.items.find(item => item.label === menuLabel)
    if (menuItem?.children) {
      estimatedMenuHeight = menuItem.children.length * 40 + 16 // 40px per item + 16px padding
    }
  }
  
  let top = rect.top
  const left = rect.right + 4 // 4px gap
  
  // Check if menu would overflow bottom of viewport
  if (top + estimatedMenuHeight > viewportHeight) {
    // Adjust so bottom of menu aligns with bottom of viewport (with 8px margin)
    top = viewportHeight - estimatedMenuHeight - 8
    // Ensure top doesn't go above viewport
    if (top < 8) top = 8
  }
  
  return { top, left }
}

const toggleMenu = (label: string, event: Event) => {
  if (openMenu.value === label) {
    openMenu.value = null
  } else {
    const el = menuRefs.value[label]
    if (el) {
      menuPositions.value[label] = calculatePosition(el, label)
    }
    openMenu.value = label
  }
}

const handleMouseEnter = (label: string, event: Event) => {
  if (closeTimeout) {
    clearTimeout(closeTimeout)
    closeTimeout = null
  }
  
  // Calculate position based on the menu item
  const el = menuRefs.value[label]
  if (el) {
    menuPositions.value[label] = calculatePosition(el, label)
  }
  
  openMenu.value = label
}

const handleMouseLeave = () => {
  closeTimeout = setTimeout(() => {
    openMenu.value = null
    openChildMenu.value = null
  }, 150)
}

const handleChildMouseEnter = (label: string, event: Event) => {
  if (closeChildTimeout) {
    clearTimeout(closeChildTimeout)
    closeChildTimeout = null
  }
  if (closeTimeout) {
    clearTimeout(closeTimeout)
    closeTimeout = null
  }
  
  // Calculate position for child popup
  const el = childMenuRefs.value[label]
  if (el) {
    const rect = el.getBoundingClientRect()
    const viewportHeight = window.innerHeight
    
    // Find child item to estimate menu height
    let estimatedMenuHeight = 150
    for (const menuItem of props.items) {
      if (menuItem.children) {
        const childItem = menuItem.children.find(c => c.label === label)
        if (childItem?.children) {
          estimatedMenuHeight = childItem.children.length * 40 + 16
          break
        }
      }
    }
    
    let top = rect.top
    const left = rect.right + 4
    
    // Check if menu would overflow bottom of viewport
    if (top + estimatedMenuHeight > viewportHeight) {
      top = viewportHeight - estimatedMenuHeight - 8
      if (top < 8) top = 8
    }
    
    childMenuPositions.value[label] = { top, left }
  }
  
  openChildMenu.value = label
}

const handleChildMouseLeave = () => {
  closeChildTimeout = setTimeout(() => {
    openChildMenu.value = null
  }, 150)
}

const handleItemClick = () => {
  openMenu.value = null
  openChildMenu.value = null
  emit('itemClick')
}
</script>
