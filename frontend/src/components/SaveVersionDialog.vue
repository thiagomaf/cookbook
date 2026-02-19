<template>
  <Dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    header="Save Version"
    modal
    style="width: min(360px, 95vw)"
  >
    <p style="color: var(--p-text-muted-color); font-size: 0.9rem; margin: 0; line-height: 1.5">
      This will create an immutable snapshot committed to git.
      You can rate this version later, after you cook and taste it.
    </p>

    <template #footer>
      <Button label="Cancel" text @click="emit('update:visible', false)" />
      <Button
        label="Save Version"
        icon="pi pi-check"
        :loading="saving"
        @click="emit('save')"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

defineProps<{ visible: boolean; saving?: boolean }>()
const emit = defineEmits<{
  'update:visible': [boolean]
  save: []
}>()
</script>
