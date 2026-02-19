<template>
  <div style="display: flex; gap: 0.5rem; align-items: center">
    <!-- Name -->
    <InputText v-model="local.name" placeholder="Ingredient name" style="flex: 1" @input="emit('change')" />

    <!-- Quantity with tweak buttons -->
    <div style="display: flex; align-items: center; gap: 0.25rem">
      <Button
        icon="pi pi-minus"
        text
        rounded
        size="small"
        @click="tweak(-1)"
        v-tooltip.top="`-${props.tweakPct}%`"
      />
      <InputNumber
        v-model="local.quantity"
        :min="0"
        :maxFractionDigits="3"
        :inputStyle="{ width: '80px', textAlign: 'center' }"
        @update:modelValue="emit('change')"
      />
      <Button
        icon="pi pi-plus"
        text
        rounded
        size="small"
        @click="tweak(1)"
        v-tooltip.top="`+${props.tweakPct}%`"
      />
    </div>

    <!-- Unit -->
    <InputText v-model="local.unit" placeholder="g" style="width: 56px" @input="emit('change')" />

    <!-- Remove -->
    <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="emit('remove')" />
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { Ingredient } from '@/types'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'

const props = defineProps<{ modelValue: Ingredient; tweakPct: number }>()
const emit = defineEmits<{
  'update:modelValue': [Ingredient]
  remove: []
  change: []
}>()

const local = reactive({ ...props.modelValue })

watch(() => props.modelValue, (v) => { Object.assign(local, v) }, { deep: true })
watch(local, () => emit('update:modelValue', { ...local }), { deep: true })

function tweak(direction: 1 | -1) {
  const factor = props.tweakPct / 100
  const delta = (local.quantity || 0) * factor
  const newQty = (local.quantity || 0) + direction * delta
  local.quantity = parseFloat(Math.max(0, newQty).toFixed(3))
  emit('change')
}
</script>
