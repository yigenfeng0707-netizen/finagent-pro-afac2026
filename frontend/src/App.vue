<template>
  <div class="flex h-screen overflow-hidden">
    <!-- 侧边栏 -->
    <Sidebar />
    <!-- 主内容区 -->
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
    <!-- 右侧预警面板 -->
    <AlertPanel v-if="showAlertPanel" @close="showAlertPanel = false" />
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Sidebar from './components/Sidebar.vue'
import AlertPanel from './components/AlertPanel.vue'

const showAlertPanel = ref(false)
provide('toggleAlertPanel', () => { showAlertPanel.value = !showAlertPanel.value })
</script>
