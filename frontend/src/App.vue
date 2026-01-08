<template>
  <div id="app">
    <!-- Sidebar -->
    <GameSidebar />

    <!-- Main Content -->
    <div class="main-content">
      <nav class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.name"
          :class="{ active: activeTab === tab.name }"
          @click="selectTab(tab.name)"
        >
          {{ tab.label }}
        </button>
      </nav>

      <div class="tab-content">
        <ConsoleTab v-if="activeTab === 'Console'" />
        <CharacterTab v-if="activeTab === 'Character'" />
        <InventoryTab v-if="activeTab === 'Inventory'" />
        <LoreTab v-if="activeTab === 'Lore'" />
        <StatusTab v-if="activeTab === 'Status'" />
        <SettingsTab v-if="activeTab === 'Settings'" />
      </div>
    </div>
  </div>
</template>

<script>
import GameSidebar from "./components/GameSidebar.vue";
import ConsoleTab from "./components/tabs/ConsoleTab.vue";
import CharacterTab from "./components/tabs/CharacterTab.vue";
import InventoryTab from "./components/tabs/InventoryTab.vue";
import LoreTab from "./components/tabs/LoreTab.vue";
import StatusTab from "./components/tabs/StatusTab.vue";
import SettingsTab from "./components/tabs/SettingsTab.vue";

export default {
  name: "App",
  components: {
    GameSidebar,
    ConsoleTab, 
    CharacterTab,
    InventoryTab,
    LoreTab,
    StatusTab,
    SettingsTab,
  },
  data() {
    return {
      tabs: [
        { name: "Console", label: "Console" },
        { name: "Character", label: "Char" },
        { name: "Inventory", label: "Inv" },
        { name: "Lore", label: "Lore" },
        { name: "Status", label: "Status" },
        { name: "Settings", label: "Settings" },
      ],
      activeTab: "Console", // Default tab is Console
    };
  },
  methods: {
    selectTab(tabName) {
      this.activeTab = tabName;
    },
  },
};
</script>

<style scoped>
/* General Layout */
#app {
  display: flex;
}
.main-content {
  flex: 1;
  padding: 20px;
  background: #121212;
  color: white;
}

/* Tabs Styling */
.tabs {
  display: flex;
  margin-bottom: 20px;
  background: #1e1e1e;
  padding: 10px;
  border-bottom: 2px solid #444;
}
.tabs button {
  flex: 1;
  padding: 10px 15px;
  border: none;
  background: #333;
  color: white;
  cursor: pointer;
  text-align: center;
  font-size: 1rem;
  border-radius: 5px 5px 0 0;
  margin-right: 5px;
}
.tabs button.active {
  background: #4caf50;
  font-weight: bold;
}
.tabs button:hover {
  background: #555;
}

/* Content Section */
.tab-content {
  background: #1e1e1e;
  padding: 15px;
  border-radius: 5px;
  color: white;
}
</style>