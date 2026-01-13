<template>
  <div class="console-tab">
    <!-- Story Display Area -->
    <div class="story-area" ref="storyArea">
      <div
        v-for="(entry, index) in story"
        :key="index"
        :class="{
          'player-command': entry.startsWith('>'),
          'gm-response': entry.startsWith('GM:')
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
import { EventBus } from "@/utils/EventBus"; // EventBus for communication with StatusTab

export default {
  name: "ConsoleTab",
  props: {
    updateGameState: Function, // Updates game state in parent
    gameState: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      story: ["[GM in Debug Mode] Welcome to the RPG Tester!"],
      playerInput: "",
      apiUrl: "http://127.0.0.1:8000/api/gm", // Backend URL
      debugMode: true, // Enables debug functionality for testing
    };
  },
  methods: {
    /**
     * Handles player commands and routes them for Debug or API processing.
     */
    async sendCommand() {
      if (this.playerInput.trim() === "") {
        this.story.push("GM: Please enter a valid command.");
        this.scrollToBottom();
        this.saveStoryToLocalStorage();
        return;
      }

      this.story.push(`> ${this.playerInput}`);

      if (this.debugMode) {
        this.processDebugCommand(this.playerInput); // Debug command processing
        this.playerInput = ""; // Clear input box
        this.scrollToBottom();
        this.saveStoryToLocalStorage();
        return;
      }

      // Sends the command to backend for processing
      try {
        const response = await axios.post(this.apiUrl, { prompt: this.playerInput });
        if (response.data.response) {
          this.story.push(`GM: ${response.data.response}`);
        } else {
          this.story.push("GM: No response received from server.");
        }

        if (response.data.game_state) {
          this.updateGameState(response.data.game_state);
        }
      } catch (error) {
        console.error("[ConsoleTab] Backend Error:", error);
        this.story.push("GM: Error while processing your command.");
      }

      this.playerInput = "";
      this.scrollToBottom();
      this.saveStoryToLocalStorage();
    },

    /**
     * Debug Command Processor (local testing).
     */
    processDebugCommand(command) {
      const updatedGameState = structuredClone(this.gameState || {});
      const player = updatedGameState.player || {
        hp: 100,
        hp_max: 100,
        mana: 50,
        mana_max: 50,
        stamina: 50,
        stamina_max: 50,
      };

      switch (command.toLowerCase()) {
        case "attack":
          this.story.push("GM: You attacked the dummy. Stamina reduced by 10.");
          player.stamina = Math.max(player.stamina - 10, 0);
          break;

        case "heal":
          this.story.push("GM: You healed yourself. Restored 20 HP.");
          player.hp = Math.min(player.hp + 20, player.hp_max);
          break;

        case "damage":
          this.story.push("GM: You took 15 damage.");
          player.hp = Math.max(player.hp - 15, 0);
          break;

        case "rest":
          this.story.push("GM: You rested. Restored 50 HP, Mana, and Stamina.");
          player.hp = Math.min(player.hp + 50, player.hp_max);
          player.mana = Math.min(player.mana + 50, player.mana_max);
          player.stamina = Math.min(player.stamina + 50, player.stamina_max);
          break;

        case "status":
          this.story.push(
            `GM: Status - HP ${player.hp}/${player.hp_max}, Stamina ${player.stamina}/${player.stamina_max}, Mana ${player.mana}/${player.mana_max}`
          );
          break;

        default:
          this.handleCustomCommands(command);
      }

      this.updateGameState(updatedGameState);
    },

    /**
     * Handles condition-related commands (e.g., apply {conditionName}).
     */
    handleCustomCommands(command) {
      const conditionMatch = command.match(/^apply (\w+)$/i);
      if (conditionMatch) {
        this.applyCondition(conditionMatch[1]);
        return;
      }

      this.story.push(`[GM (Debug)] Unknown command: "${command}".`);
    },

    /**
     * Emits the given condition event via EventBus.
     */
    applyCondition(conditionName) {
      const conditions = {
        exhausted: {
          name: "Exhausted",
          description: "You feel drained. Movement halved.",
          duration: 4,
          type: "debuff",
        },
        blessed: {
          name: "Blessed",
          description: "Holy protection increases WIS by 3.",
          duration: 3,
          type: "buff",
        },
      };

      const selectedCondition = conditions[conditionName.toLowerCase()];
      if (!selectedCondition) {
        this.story.push(`[GM (Debug)] Unknown condition: "${conditionName}".`);
        return;
      }

      EventBus.emit("add-condition", selectedCondition); // Emit condition event
      this.story.push(`[GM (Debug)] Applied condition: "${selectedCondition.name}".`);
    },

    /**
     * Keeps the story view scrolled to the last message.
     */
    scrollToBottom() {
      const storyArea = this.$refs.storyArea;
      if (storyArea) {
        storyArea.scrollTo(0, storyArea.scrollHeight);
      }
    },

    /**
     * Saves the console story data to localStorage.
     */
    saveStoryToLocalStorage() {
      try {
        localStorage.setItem("consoleStory", JSON.stringify(this.story));
      } catch (error) {
        console.error("[ConsoleTab] Failed to save story:", error);
      }
    },

    /**
     * Loads the story data from localStorage when mounted.
     */
    loadStoryFromLocalStorage() {
      try {
        const savedStory = localStorage.getItem("consoleStory");
        if (savedStory) {
          this.story = JSON.parse(savedStory);
        }
      } catch (error) {
        console.error("[ConsoleTab] Failed to load story:", error);
      }
    },
  },
  mounted() {
    this.loadStoryFromLocalStorage();
    this.scrollToBottom();
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
  border-radius: 5px;
  background-color: #151515;
}
.story-entry {
  margin-bottom: 10px;
}
.player-command {
  color: #81c784;
}
.gm-response {
  color: #ffb74d;
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
  border-radius: 5px;
}
button:hover {
  background-color: #45a049;
}
</style>