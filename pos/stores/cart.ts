import { defineStore } from 'pinia'

interface CartItem {
    product_id: string
    name: string
    unit_price: number
    quantity: number
    image_url?: string
}

interface Promo {
    code: string
    name: string
    discount: number
}

export const useCartStore = defineStore('cart', {
    state: () => ({
        items: [] as CartItem[],
        customer: null as any,
        promo: null as Promo | null,
        taxRate: 0.1  // 10% tax
    }),

    getters: {
        itemCount: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),

        subtotal: (state) => state.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0),

        discount: (state) => state.promo?.discount || 0,

        tax(state): number {
            return (this.subtotal - this.discount) * state.taxRate
        },

        total(): number {
            return this.subtotal - this.discount + this.tax
        }
    },

    actions: {
        addItem(product: { id: string, name: string, unit_price: number, image_url?: string }) {
            const existing = this.items.find(item => item.product_id === product.id)
            if (existing) {
                existing.quantity++
            } else {
                this.items.push({
                    product_id: product.id,
                    name: product.name,
                    unit_price: product.unit_price,
                    quantity: 1,
                    image_url: product.image_url
                })
            }
        },

        removeItem(productId: string) {
            const index = this.items.findIndex(item => item.product_id === productId)
            if (index > -1) {
                this.items.splice(index, 1)
            }
        },

        updateQuantity(productId: string, quantity: number) {
            const item = this.items.find(i => i.product_id === productId)
            if (item) {
                if (quantity <= 0) {
                    this.removeItem(productId)
                } else {
                    item.quantity = quantity
                }
            }
        },

        incrementQuantity(productId: string) {
            const item = this.items.find(i => i.product_id === productId)
            if (item) {
                item.quantity++
            }
        },

        decrementQuantity(productId: string) {
            const item = this.items.find(i => i.product_id === productId)
            if (item) {
                if (item.quantity > 1) {
                    item.quantity--
                } else {
                    this.removeItem(productId)
                }
            }
        },

        setCustomer(customer: any) {
            this.customer = customer
        },

        setPromo(promo: Promo | null) {
            this.promo = promo
        },

        clearCart() {
            this.items = []
            this.customer = null
            this.promo = null
        }
    }
})
