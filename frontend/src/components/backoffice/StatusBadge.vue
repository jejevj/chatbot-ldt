<template>
  <span :class="styles[status] || styles.default" class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium">
    <span class="w-1.5 h-1.5 rounded-full" :class="dot[status] || dot.default" />
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ status: { type: String, default: 'default' } })

const map = {
  ready:      { label: 'Ready',      style: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',  dot: 'bg-emerald-400' },
  processing: { label: 'Processing', style: 'bg-amber-500/20  text-amber-300  border border-amber-500/30',    dot: 'bg-amber-400 animate-pulse' },
  error:      { label: 'Error',      style: 'bg-red-500/20    text-red-300    border border-red-500/30',       dot: 'bg-red-400' },
  applied:    { label: 'Applied',    style: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30', dot: 'bg-emerald-400' },
  pending:    { label: 'Pending',    style: 'bg-zinc-500/20   text-zinc-300   border border-zinc-500/30',      dot: 'bg-zinc-400' },
  active:     { label: 'Aktif',      style: 'bg-sky-500/20    text-sky-300    border border-sky-500/30',       dot: 'bg-sky-400' },
  inactive:   { label: 'Nonaktif',   style: 'bg-zinc-500/20   text-zinc-300   border border-zinc-500/30',      dot: 'bg-zinc-400' },
}

const label  = computed(() => map[props.status]?.label  || props.status)
const styles = computed(() => Object.fromEntries(Object.entries(map).map(([k,v]) => [k, v.style])))
const dot    = computed(() => Object.fromEntries(Object.entries(map).map(([k,v]) => [k, v.dot])))
</script>
