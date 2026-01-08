<template>
  <aside class="sidebar">

    <!-- Stats Section -->
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

    <!-- Divine Favor -->
    <p><strong>Divine Favor:</strong> {{ divineFavor }}</p>
    <hr />

    <!-- Attributes Grid -->
    <h2>Attributes</h2>
    <div class="attributes-grid">
      <div v-for="attribute in attributes" :key="attribute.name" class="attribute-box">
        <p class="attribute-name">{{ attribute.name }}</p>
        <p class="attribute-value">{{ attribute.value }}</p>
      </div>
    </div>
    <hr />

    <!-- Vexal Section -->
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
        :class="{ filled: index < vexalSubjugation }"
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
import ProgressBar from './ProgressBar.vue';

export default {
  name: 'GameSidebar',
  components: {
    ProgressBar,
  },
  props: {
    gameState: Object, // Parent will pass this down for dynamic updates
  },
  data() {
    return {
      stats: [
        { name: 'Health', currentValue: 80, maxValue: 100, color: '#ff4b4b' },
        { name: 'Mana', currentValue: 50, maxValue: 100, color: '#28a745' },
        { name: 'Stamina', currentValue: 65, maxValue: 100, color: '#ff9800' },
      ],
      divineFavor: 20, // Example data for Divine Favor
      attributes: [
        { name: 'STR', value: 10 },
        { name: 'DEX', value: 12 },
        { name: 'CON', value: 11 },
        { name: 'WIS', value: 14 },
        { name: 'INT', value: 16 },
        { name: 'CHA', value: 9 },
      ],
      vexalStatus: 'Idle',
      vexalArousal: 45,
      vexalSubjugation: 5,
      skills: ['Jump', 'Climb', 'Persuade', 'Attack Goblins'], // Example skills
      spells: ['Fireball', 'Heal', 'Shield', 'Lightning Bolt'], // Example spells
      selectedSkill: '',
      selectedSpell: '',
      impromptuAction: '',
    };
  },
  watch: {
    gameState: {
      deep: true,
      immediate: true,
      handler(newState) {
        this.syncWithGameState(newState);
      },
    },
  },
  methods: {
    /**
     * Sync data from the gameState into the Vue component dynamically.
     */
    updateState(state) {
      if (!state || !state.player) {
        console.warn('GameState is invalid or missing player data.');
        return;
      }

      // Sync stats
      const { hp, hp_max, mana, mana_max, stamina, stamina_max } = state.player;
      this.stats = [
        { name: 'Health', currentValue: hp, maxValue: hp_max, color: '#ff4b4b' },
        { name: 'Mana', currentValue: mana, maxValue: mana_max, color: '#28a745' },
        { name: 'Stamina', currentValue: stamina, maxValue: stamina_max, color: '#ff9800' },
      ];

      // Sync Divine Favor
      this.divineFavor = state.player.divineFavor || 0;

      // Sync attributes
      this.attributes = Object.entries(state.player.attributes).map(([name, value]) => ({
        name,
        value,
      }));

      // Sync Vexal properties
      this.vexalStatus = state.vexal?.status || 'Idle';
      this.vexalArousal = state.vexal?.arousal || 0;
      this.vexalSubjugation = state.vexal?.sub_peak || 0;

      // Sync actions
      this.skills = state.player.skills || [];
      this.spells = state.player.spells || [];
    },
    syncWithGameState(state) {
      this.updateState(state); // Use the `updateState` helper for syncing
    },
    useSkill() {
      if (!this.selectedSkill.trim()) {
        alert('Please select a skill first!');
        return;
      }
      console.log(`Used skill: ${this.selectedSkill}`);
      this.selectedSkill = '';
    },
    useSpell() {
      if (!this.selectedSpell.trim()) {
        alert('Please select a spell first!');
        return;
      }
      console.log(`Used spell: ${this.selectedSpell}`);
      this.selectedSpell = '';
    },
    performImpromptuAction() {
      if (!this.impromptuAction.trim()) {
        alert('Please enter a valid action.');
        return;
      }
      console.log(`Performed action: ${this.impromptuAction}`);
      this.impromptuAction = '';
    },
  },
};
</script>

<style scoped>
/* Sidebar Container */
.sidebar {
  width: 25%;
  background-color: #0e1117;
  padding: 15px;
  color: white;
  overflow-y: auto;
}

h2 {
  border-bottom: 2px solid #333;
  margin-bottom: 10px;
  padding-bottom: 5px;
}

hr {
  border: 1px solid #333;
  margin: 15px 0;
}

/* Stats Section */
.stat-item {
  margin-bottom: 10px;
}

/* Attributes Grid */
.attributes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* 2 columns for 6 attributes */
  gap: 15px;
}

.attribute-box {
  background-color: #1e1e1e;
  padding: 10px;
  text-align: center;
  border-radius: 5px;
  border: 1px solid #444;
}

.attribute-name {
  font-size: 0.85rem;
  color: #999;
}

.attribute-value {
  font-size: 1.2rem;
  font-weight: bold;
}

/* Vexal Section */
.subjugation-peak {
  display: flex;
  justify-content: space-between;
}

.subjugation-box {
  width: 15px;
  height: 15px;
  background: #444;
  border-radius: 3px;
}

.subjugation-box.filled {
  background-color: #e83e8c;
}

/* Dropdowns and Inputs */
.select-dropdown,
.action-input {
  width: 100%;
  padding: 10px;
  margin-top: 5px;
  border: 1px solid #444;
  border-radius: 5px;
  background-color: #1e1e1e;
  color: white;
}
</style>