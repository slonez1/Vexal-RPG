<template>
  <div class="console-tab">
    <!-- Story Display Area -->
    <div class="story-area" ref="storyArea">
      <div
        v-for="(entry, index) in story"
        :key="index"
        :class="{
          'player-command': entry.startsWith('>'),
          'gm-response': entry.startsWith('GM:'),
        }"
        class="story-entry"
      >
        <p>{{ entry }}</p>
      </div>
    </div>

    <!-- Command Input Area -->
    <div class="command-input">
      <input
        type="text"
        v-model="playerInput"
        placeholder="Enter your command..."
        @keyup.enter="sendCommand"
      />
      <button @click="sendCommand">Go</button>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "ConsoleTab",
  props: ["updateGameState"], // Pass function to notify the parent to update states dynamically
  data() {
    return {
      story: ["Welcome to the RPG!"],
      playerInput: "",
      apiUrl: "http://127.0.0.1:8000/api/gm",
      stateUrl: "http://127.0.0.1:8000/api/state",
    };
  },
  methods: {
    async sendCommand() {
      if (this.playerInput.trim() === "") {
        this.story.push("GM: Please provide a valid command!");
        this.scrollToBottom();
        return;
      }

      this.story.push(`> ${this.playerInput}`);

      try {
        // Send the GM command
        const response = await axios.post(this.apiUrl, { prompt: this.playerInput });

        if (response.data.response) {
          this.story.push(`GM: ${response.data.response}`);
        } else {
          this.story.push("GM: No response received from the server.");
        }

        // Fetch updated game state and notify parent
        const stateResponse = await axios.get(this.stateUrl);
        this.updateGameState(stateResponse.data); // Notify parent about the updated state
      } catch (error) {
        console.error("Error:", error);
        this.story.push("GM: Unable to process command.");
      }

      this.playerInput = "";
      this.scrollToBottom();
    },
    scrollToBottom() {
      const storyArea = this.$refs.storyArea;
      if (storyArea) {
        storyArea.scrollTop = storyArea.scrollHeight;
      }
    },
  },
};
</script>

<style scoped>
.console-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #1e1e1e;
  color: #dcdcdc;
}

.story-area {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  border: 1px solid #333333;
}

.command-input {
  display: flex;
  margin-top: 10px;
}

button {
  margin-left: 10px;
  padding: 10px;
  background-color: #4caf50;
  color: white;
  border: none;
  cursor: pointer;
}
</style>