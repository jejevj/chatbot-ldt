<template>
  <BackofficeLayout>
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-bo-100">AI Management</h1>
      <p class="text-bo-300 text-sm mt-0.5">Kelola dokumen RAG, FAQ, dan koreksi jawaban AI</p>
    </div>

    <!-- Tab Nav -->
    <div class="flex gap-1 mb-6 bo-glass p-1">
      <button
        v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
          activeTab === tab.key
            ? 'bg-bo-800 text-white shadow'
            : 'text-bo-300 hover:text-white hover:bg-white/10'
        ]"
      >
        <component :is="tab.icon" :size="15" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Dokumen -->
    <div v-if="activeTab === 'documents'">
      <DocumentsTab />
    </div>

    <!-- Tab: FAQ -->
    <div v-if="activeTab === 'faq'">
      <FAQTab />
    </div>

    <!-- Tab: Feedback -->
    <div v-if="activeTab === 'feedback'">
      <FeedbackTab />
    </div>
  </BackofficeLayout>
</template>

<script setup>
import { ref } from 'vue'
import { FileText, HelpCircle, MessageSquareWarning } from 'lucide-vue-next'
import BackofficeLayout from '../../components/backoffice/BackofficeLayout.vue'
import DocumentsTab from '../../components/backoffice/tabs/DocumentsTab.vue'
import FAQTab       from '../../components/backoffice/tabs/FAQTab.vue'
import FeedbackTab  from '../../components/backoffice/tabs/FeedbackTab.vue'

const activeTab = ref('documents')
const tabs = [
  { key: 'documents', label: 'Dokumen RAG',   icon: FileText },
  { key: 'faq',       label: 'FAQ',            icon: HelpCircle },
  { key: 'feedback',  label: 'Koreksi AI',     icon: MessageSquareWarning },
]
</script>
