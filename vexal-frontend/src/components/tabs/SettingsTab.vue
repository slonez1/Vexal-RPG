<template>
  <div class="settings-tab">
    <div class="settings-layout">
      <!-- Audio Settings -->
      <section class="audio-settings">
        <h2>Audio Settings</h2>

        <div class="audio-toggle">
          <label for="audio"><strong>Audio:</strong></label>
          <input
            type="checkbox"
            id="audio"
            v-model="audioEnabled"
            @change="toggleAudio"
          />
          <span>{{ audioEnabled ? "ON" : "OFF" }}</span>
        </div>

        <div class="voice-select">
          <label for="voice"><strong>Voice Option:</strong></label>
          <select id="voice" v-model="selectedVoice" @change="updateVoice">
            <option v-for="voice in voiceOptions" :key="voice" :value="voice">
              {{ voice }}
            </option>
          </select>
        </div>

        <div class="speed-toggle">
          <label><strong>Speech Speed:</strong></label>
          <button @click="decreaseSpeed" :disabled="speechSpeed <= minSpeed">-</button>
          <span>{{ speechSpeed.toFixed(2) }}x</span>
          <button @click="increaseSpeed" :disabled="speechSpeed >= maxSpeed">+</button>
        </div>
      </section>

      <hr />

      <!-- Game Management -->
      <section class="game-management">
        <h2>Game Management</h2>
        <div class="game-buttons">
          <button @click="saveGame">Save Game</button>
          <button @click="loadGame">Load Game</button>
          <button @click="restartGame">Restart Game</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  name: "SettingsTab",
  data() {
    return {
      // Audio Settings
      audioEnabled: true,
      voiceOptions: ["Narrator 1", "Narrator 2", "Narrator 3"],
      selectedVoice: "Narrator 1",

      // Speech Speed
      speechSpeed: 1.0, // Default value
      minSpeed: 0.5,
      maxSpeed: 3.0,
    };
  },
  methods: {
    toggleAudio() {
      console.log(`Audio is now ${this.audioEnabled ? "ON" : "OFF"}`);
    },
    updateVoice() {
      console.log(`Selected Voice: ${this.selectedVoice}`);
    },
    increaseSpeed() {
      if (this.speechSpeed < this.maxSpeed) {
        this.speechSpeed += 0.25;
        console.log(`Speech Speed: ${this.speechSpeed.toFixed(2)}x`);
      }
    },
    decreaseSpeed() {
      if (this.speechSpeed > this.minSpeed) {
        this.speechSpeed -= 0.25;
        console.log(`Speech Speed: ${this.speechSpeed.toFixed(2)}x`);
      }
    },
    saveGame() {
      console.log("Game saved!");
    },
    loadGame() {
      console.log("Game loaded!");
    },
    restartGame() {
      console.log("Game restarted!");
    },
  },
};
</script>

<style scoped>
/* Settings Layout */
.settings-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

/* Section Headers */
.settings-layout h2 {
  margin-bottom: 15px;
  border-bottom: 1px solid #444;
  padding-bottom: 5px;
}

/* Audio Settings */
.audio-settings .audio-toggle,
.audio-settings .voice-select,
.audio-settings .speed-toggle {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}
.audio-settings select {
  background: #333;
  color: white;
  padding: 5px;
  border: 1px solid #444;
  border-radius: 5px;
}
.speed-toggle button {
  background: #4caf50;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 5px;
  cursor: pointer;
}
.speed-toggle span {
  margin: 0 10px;
  font-weight: bold;
}
.speed-toggle button:disabled {
  background: #555;
  color: #aaa;
  cursor: not-allowed;
}

/* Game Management */
.game-management .game-buttons button {
  background: #4caf50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  margin-right: 10px;
}
</style>