<template>
  <div id="app">
    <GameSidebar :gameState="gameState" />

    <div class="main-content">
      <!-- Tab Navigation -->
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

      <!-- Tab Content -->
      <div class="tab-content">
        <ConsoleTab
          v-if="activeTab === 'Console'"
          :updateGameState="updateGameState"
          :gameState="gameState"
        />
        <CharacterTab v-if="activeTab === 'Character'" :gameState="gameState" />
        <InventoryTab v-if="activeTab === 'Inventory'" :gameState="gameState" />
        <LoreTab v-if="activeTab === 'Lore'" />
        <StatusTab v-if="activeTab === 'Status'" :gameState="gameState" />
        <SettingsTab v-if="activeTab === 'Settings'" />
      </div>
    </div>
  </div>
</template>

<script>
import { db } from "./firebase"; // Firestore instance (Firebase setup)
import {
  doc,
  getDoc,
  setDoc,
} from "firebase/firestore";

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
      gameState: null, // Centralized game state
      tabs: [
        { name: "Console", label: "Console" },
        { name: "Character", label: "Char" },
        { name: "Inventory", label: "Inventory" },
        { name: "Lore", label: "Lore" },
        { name: "Status", label: "Status" },
        { name: "Settings", label: "Settings" },
      ],
      activeTab: "Console", // Default active tab
      gameDocumentRef: null, // Firestore Document Reference
    };
  },
  methods: {
    /**
     * Initializes Firestore and state persistence setup.
     */
    async initializeGameState() {
      try {
        // Define Firestore document reference
        this.gameDocumentRef = doc(db, "sessions", "rpg_game_state");

        // Restore gameState from localStorage or Firestore
        let savedGameState = this.getStateFromLocalStorage();
        if (!savedGameState) {
          console.log("[App] No local state found, fetching from Firestore...");
          savedGameState = await this.fetchGameStateFromFirestore();
        }

        // Fallback to default state if necessary
        if (!savedGameState) {
          console.warn("[App] No game state found in Firestore, initializing default state...");
          savedGameState = this.getDefaultGameState();
        }

        // Apply the game state
        this.replaceGameState(savedGameState);
      } catch (error) {
        console.error("[App] Error during game state initialization:", error);
      }
    },

    /**
     * Fetches the current `gameState` from Firestore.
     */
    async fetchGameStateFromFirestore() {
      try {
        if (!this.gameDocumentRef) {
          throw new Error("[App] Firestore reference not initialized.");
        }

        const docSnap = await getDoc(this.gameDocumentRef);
        if (docSnap.exists()) {
          console.log("[App] Fetched game state from Firestore:", docSnap.data());
          return docSnap.data();
        } else {
          console.warn("[App] No gameState found in Firestore.");
          return null;
        }
      } catch (error) {
        console.error("[App] Error fetching gameState from Firestore:", error);
        return null;
      }
    },

    /**
     * Saves the current `gameState` to Firestore.
     */
    async saveGameStateToFirestore(newState) {
      try {
        await setDoc(this.gameDocumentRef, newState);
        console.log("[App] Game state saved to Firestore.");
      } catch (error) {
        console.error("[App] Error saving gameState to Firestore:", error);
      }
    },

    /**
     * Replaces the current gameState and saves it to localStorage.
     */
    replaceGameState(newState) {
      if (newState && typeof newState === "object") {
        this.gameState = { ...newState }; // New reference for reactivity
        this.saveStateToLocalStorage(newState);
      } else {
        console.error("[App] Invalid gameState provided:", newState);
      }
    },

    /**
     * Updates the game state (used by child components) and syncs to Firestore and localStorage.
     */
    updateGameState(newState) {
      this.replaceGameState(newState);
      this.saveGameStateToFirestore(newState);
    },

    /**
     * Retrieves gameState from localStorage.
     */
    getStateFromLocalStorage() {
      try {
        const state = localStorage.getItem("gameState");
        return state ? JSON.parse(state) : null;
      } catch (error) {
        console.error("[App] Error retrieving gameState from localStorage:", error);
        return null;
      }
    },

    /**
     * Saves gameState to localStorage.
     */
    saveStateToLocalStorage(state) {
      try {
        localStorage.setItem("gameState", JSON.stringify(state));
        console.log("[App] Game state saved to localStorage.");
      } catch (error) {
        console.error("[App] Error saving gameState to localStorage:", error);
      }
    },

    /**
     * Returns the default gameState structure.
     */
    getDefaultGameState() {
      return {
        player: {
          hp: 100,
          hp_max: 100,
          mana: 50,
          mana_max: 50,
          stamina: 50,
          stamina_max: 50,
          divineFavor: 0,
          attributes: {
            Strength: 10,
            Dexterity: 10,
            Wisdom: 10,
          },
        },
        vexal: {
          status: "Inactive",
          arousal: 0,
          sub_peak: 0,
        },
      };
    },

    /**
     * Switches between tabs.
     */
    selectTab(tabName) {
      this.activeTab = tabName;
    },
  },

  /**
   * Lifecycle Hook: After creation, initialize game state.
   */
  created() {
    this.initializeGameState();
  },
};
</script>

<style scoped>
#app {
  display: flex;
}

/* Main Content Styling */
.main-content {
  flex: 1;
  padding: 20px;
  background: #121212;
  color: white;
}

.tabs {
  display: flex;
  margin-bottom: 20px;
  background: #1e1e1e;
  padding: 10px;
}

.tabs button {
  flex: 1;
  padding: 10px;
  background: #333;
  color: white;
  cursor: pointer;
  border-radius: 5px 5px 0 0;
  margin-right: 5px;
}

.tabs button.active {
  background: #4caf50;
}
</style>