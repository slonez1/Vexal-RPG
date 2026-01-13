<template>
  <div class="status-tab">
    <div class="status-layout">
      <!-- Character Stats -->
      <div class="character-stats">
        <h2>Character</h2>
        <ul>
          <li><strong>Armor Class:</strong> {{ characterStats.armorClass }}</li>
          <li><strong>Noise:</strong> {{ characterStats.noise }}</li>
          <li><strong>Bulk:</strong> {{ characterStats.bulk }}</li>
        </ul>
      </div>

      <!-- Conditions -->
      <div class="conditions">
        <h2>Active Conditions</h2>
        <ul>
          <li
            v-for="condition in activeConditions"
            :key="condition.name"
            :class="[condition.type]"
            :style="{ borderLeft: `4px solid ${condition.color || '#333'}` }"
          >
            <p><strong>{{ condition.name }}</strong></p>
            <p>{{ condition.description }}</p>
            <p v-if="condition.duration">Duration: {{ condition.duration }} turn(s)</p>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { EventBus } from "@/utils/EventBus";

export default {
  name: "StatusTab",
  data() {
    return {
      // Character statistics to be displayed
      characterStats: {
        armorClass: 18,
        noise: 12,
        bulk: 55,
      },

      // Array to store active conditions applied to the character
      activeConditions: [],
    };
  },
  methods: {
    /**
     * Adds a new condition to the active conditions array or updates an existing one.
     * @param {Object} newCondition - The condition object containing metadata (name, type, duration, etc.)
     */
    addCondition(newCondition) {
      const existingCondition = this.activeConditions.find((cond) => cond.name === newCondition.name);

      if (!existingCondition) {
        console.log("[StatusTab] Adding new condition:", newCondition);
        this.activeConditions.push(newCondition); // Add the new condition
      } else {
        console.log("[StatusTab] Updating condition duration:", newCondition);
        this.$set(existingCondition, "duration", Math.max(existingCondition.duration, newCondition.duration));
      }
    },

    /**
     * Handles turn-end events: reduces duration of all active conditions
     * and removes those that have expired (duration <= 0).
     */
    handleTurnEnd() {
      console.log("[StatusTab]: Processing turn end.");
      this.activeConditions = this.activeConditions
        .map((condition) => ({
          ...condition,
          duration: condition.duration - 1,
        }))
        .filter((condition) => condition.duration > 0);

      console.log("[StatusTab]: Updated conditions:", this.activeConditions);
    },
  },
  mounted() {
    // Listens for the "add-condition" event emitted by the ConsoleTab component
    EventBus.on("add-condition", (condition) => {
      console.log("[StatusTab] Received condition:", condition);
      this.addCondition(condition);
    });

    // Simulates turn durations: reduces condition durations every 5 seconds
    this.turnInterval = setInterval(() => {
      this.handleTurnEnd();
    }, 5000); // Turn interval set to 5 seconds
  },
  beforeUnmount() {
    // Cleanup the EventBus listener and interval on component unmount
    EventBus.off("add-condition");
    clearInterval(this.turnInterval);
  },
};
</script>

<style scoped>
/* Layout Styling */
.status-layout {
  display: flex;
  gap: 20px;
  padding: 10px;
  background: #1e1e1e;
}

/* Character Stats Section */
.character-stats {
  flex: 1;
  padding: 15px;
  background: #2c2c2c;
  border-radius: 5px;
}
.character-stats h2 {
  color: #4caf50;
}
.character-stats ul {
  list-style: none;
  padding: 0;
}
.character-stats li {
  margin-bottom: 10px;
  font-size: 1rem; /* Adjusted for readability */
}

/* Active Conditions Section */
.conditions {
  flex: 2;
  padding: 15px;
  background: #2c2c2c;
  border-radius: 5px;
}
.conditions h2 {
  color: #ff9800;
}
.conditions ul {
  padding: 0;
  list-style: none;
}
.conditions li {
  padding: 10px;
  border-left: 4px solid;
  margin-bottom: 10px;
  background-color: #1e1e1e; /* Improves visibility */
  border-radius: 5px;
}
.buff {
  border-color: #4caf50; /* Green for buffs */
}
.debuff {
  border-color: #f44336; /* Red for debuffs */
}
</style>