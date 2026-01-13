<template>
  <aside class="sidebar">
    <!-- Player Stats Section -->
    <h2>Player Stats</h2>
    <div v-for="stat in stats" :key="stat.name" class="stat-item">
      <ProgressBar
        :label="stat.name"
        :current="stat.currentValue"
        :max="stat.maxValue"
        :color="stat.color"
      />
    </div>
    <hr />

    <!-- Divine Favor Section -->
    <p><strong>Divine Favor:</strong> {{ divineFavor }}</p>
    <hr />

    <!-- Attributes Grid Section -->
    <h2>Attributes</h2>
    <div class="attributes-grid">
      <div
        v-for="attribute in attributes"
        :key="attribute.name"
        class="attribute-box"
      >
        <p class="attribute-name">{{ attribute.name }}</p>
        <p class="attribute-value">{{ attribute.value }}</p>
      </div>
    </div>
    <hr />

    <!-- Vexal State Section -->
    <h2>Vexal Influence</h2>
    <p class="status"><strong>Status:</strong> {{ vexalStatus }}</p>
    <ProgressBar
      label="Arousal Meter"
      :current="vexalArousal"
      :max="100"
      color="#e83e8c"
    />
    <div class="subjugation-peak">
      <div
        class="subjugation-box"
        :class="{ filled: index < subjugationPeak }"
        v-for="(_, index) in 10"
        :key="index"
      ></div>
    </div>
    <hr />

    <!-- Actions Section -->
    <h2>Actions</h2>
    <div class="action">
      <label for="skills">Select Skill:</label>
      <select id="skills" v-model="selectedSkill" class="select-dropdown">
        <option v-for="skill in skills" :key="skill" :value="skill">
          {{ skill }}
        </option>
      </select>
      <button @click="useSkill">Use Skill</button>
    </div>

    <div class="action">
      <label for="spells">Select Spell:</label>
      <select id="spells" v-model="selectedSpell" class="select-dropdown">
        <option v-for="spell in spells" :key="spell" :value="spell">
          {{ spell }}
        </option>
      </select>
      <button @click="useSpell">Cast Spell</button>
    </div>

    <div class="action">
      <label for="impromptu">Custom Action:</label>
      <input
        id="impromptu"
        v-model="impromptuAction"
        type="text"
        placeholder="Enter custom action..."
        class="action-input"
      />
      <button @click="performImpromptuAction">Perform Action</button>
    </div>
  </aside>
</template>

<script>
import ProgressBar from "./ProgressBar.vue";
import { EventBus } from "@/utils/EventBus"; // Ensure this is correctly created and imported.

export default {
  name: "GameSidebar",
  components: {
    ProgressBar,
  },
  props: {
    gameState: {
      type: Object,
      required: true, // Dynamically bound `gameState` passed from parent
    },
  },
  data() {
    return {
      stats: [],
      divineFavor: 0,
      attributes: [],
      vexalStatus: "Inactive",
      vexalArousal: 0,
      subjugationPeak: 0,
      skills: [],
      spells: [],
      selectedSkill: "",
      selectedSpell: "",
      impromptuAction: "",
    };
  },
  watch: {
    /**
     * Watches for changes to `gameState` and updates local sidebar data.
     */
    gameState: {
      deep: true,
      immediate: true,
      handler(newState) {
        if (!newState || typeof newState !== "object") {
          console.warn("[GameSidebar] Invalid or empty gameState received.");
          return;
        }
        this.syncWithGameState(newState); // Sync local data fields with gameState
      },
    },
  },
  methods: {
    /**
     * Syncs values from `gameState` to local fields for the sidebar.
     */
    syncWithGameState(state) {
      if (!state.player) {
        console.warn("[GameSidebar] Missing player in gameState.");
        return;
      }

      // Sync Stats (Health, Mana, Stamina)
      const { hp, hp_max, mana, mana_max, stamina, stamina_max } = state.player;
      this.stats = [
        { name: "Health", currentValue: hp, maxValue: hp_max, color: "#ff4b4b" },
        { name: "Mana", currentValue: mana, maxValue: mana_max, color: "#28a745" },
        { name: "Stamina", currentValue: stamina, maxValue: stamina_max, color: "#ff9800" },
      ];

      // Sync Divine Favor
      this.divineFavor = state.player.divineFavor || 0;

      // Sync Attributes
      this.attributes = Object.entries(state.player.attributes || {}).map(([key, value]) => ({
        name: key,
        value,
      }));

      // Sync Vexal State
      const vexal = state.vexal || {};
      this.vexalStatus = vexal.status || "Inactive";
      this.vexalArousal = vexal.arousal || 0;
      this.subjugationPeak = vexal.sub_peak || 0;
    },

    /**
     * Handles arousal increments based on Vexal status and Subjugation mechanics.
     */
    handleArousalAndPeaks() {
      let arousalIncrement = 0;

      if (this.vexalStatus === "Inactive") {
        arousalIncrement = Math.floor(Math.random() * 5); // Random: 0–5
      } else if (this.vexalStatus === "Active") {
        arousalIncrement = Math.floor(Math.random() * 31) + 5; // Random: 5–35
      }

      if (this.vexalStatus !== "Ruined") {
        this.vexalArousal = Math.min(this.vexalArousal + arousalIncrement, 100);

        if (this.vexalArousal === 100) {
          this.subjugationPeak++;
          this.applyOrgasmAndStunConditions(); // Apply conditions when Subjugation Peak increases
          this.vexalArousal = 0; // Reset Arousal Meter
        }
      }
    },

    /**
     * Emits "Orgasm" and "Stun" conditions globally to update the status effects in the game.
     */
    applyOrgasmAndStunConditions() {
      EventBus.emit("add-condition", {
        name: "Orgasm",
        type: "debuff",
        description: "-6 to each attribute, -20 to each skill.",
        duration: 2,
      });

      EventBus.emit("add-condition", {
        name: "Stun",
        type: "debuff",
        description: "Unable to perform actions this turn. Hit 'Go' to continue.",
        duration: 1,
      });
    },
  },
};
</script>

<style scoped>
/* Sidebar styling */
.sidebar {
  width: 25%;
  background-color: #0e1117;
  padding: 15px;
  color: #fff;
  overflow-y: auto;
  border-right: 2px solid #333;
}
h2 {
  border-bottom: 2px solid #333;
  margin-bottom: 10px;
  padding-bottom: 5px;
}
.stat-item,
.attributes-grid,
.subjugation-peak {
  margin-top: 15px;
}
button {
  margin-top: 10px;
  padding: 10px;
  background: #4caf50;
  border: none;
  border-radius: 5px;
  color: #fff;
  cursor: pointer;
}
button:hover {
  background-color: #45a049;
}
</style>