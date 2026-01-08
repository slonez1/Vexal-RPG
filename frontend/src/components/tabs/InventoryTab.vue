<template>
  <div class="inventory-tab">
    <div class="inventory-layout">
      <!-- Left: Equipment Slots -->
      <div class="equipment-panel">
        <h2>Equipment</h2>
        <div class="person-outline">
          <div
            v-for="slot in equipmentSlots"
            :key="slot.name"
            class="item-slot"
            :class="slot.name"
          >
            <p class="slot-label">{{ slot.label }}</p>
            <div v-if="slot.item" class="item-details">
              <p><strong>{{ slot.item.name }}</strong></p>
              <p>Material: {{ slot.item.material }}</p>
              <p>Armor: {{ slot.item.armorValue || 'N/A' }}</p>
              <p>Condition: {{ slot.item.condition }} / 100</p>
              <p>Weight: {{ slot.item.weight }}</p>
              <p>Bulk: {{ slot.item.bulk }}</p>
            </div>
            <div v-else class="empty-slot">[Empty]</div>
          </div>
        </div>
      </div>

      <!-- Right: Bag Inventory -->
      <div class="inventory-panel">
        <h2>Bags</h2>
        <div
          v-for="bag in bags"
          :key="bag.name"
          class="bag"
        >
          <h3>{{ bag.label }}</h3>
          <p class="bag-capacity"><strong>Capacity:</strong> {{ bag.currentBulk }} / {{ bag.maxBulk }}</p>
          <ul class="bag-items">
            <li
              v-for="item in bag.items"
              :key="item.name"
              class="bag-item"
            >
              <p><strong>{{ item.name }}</strong></p>
              <p>Material: {{ item.material }}</p>
              <p>Armor: {{ item.armorValue || 'N/A' }} | Damage: {{ item.damage || 'N/A' }}</p>
              <p>Condition: {{ item.condition }} / 100</p>
              <p>Weight: {{ item.weight }} | Bulk: {{ item.bulk }} | Noise: {{ item.noise }}</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "InventoryTab",
  data() {
    return {
      equipmentSlots: [
        { name: "head", label: "Head", item: { name: "Steel Helmet", material: "Steel", armorValue: 10, condition: 90, weight: 5, bulk: 3 } },
        { name: "torso", label: "Torso", item: { name: "Steel Breastplate", material: "Steel", armorValue: 30, condition: 85, weight: 25, bulk: 20 } },
        { name: "legs", label: "Legs", item: null },
        { name: "hands", label: "Hands", item: { name: "Leather Gloves", material: "Leather", armorValue: 5, condition: 95, weight: 2, bulk: 1 } },
        { name: "feet", label: "Feet", item: { name: "Iron Boots", material: "Iron", armorValue: 7, condition: 70, weight: 10, bulk: 5 } },
        { name: "mainHand", label: "Main Hand", item: { name: "Steel Sword", material: "Steel", damage: "1d8", condition: 85, weight: 12, bulk: 8 } },
        { name: "offHand", label: "Off Hand", item: { name: "Small Shield", material: "Wood", armorValue: 15, condition: 75, weight: 8, bulk: 6 } },
        { name: "scabbard", label: "Scabbard", item: null },
        { name: "beltPouch", label: "Belt Pouch", item: null },
        { name: "satchel", label: "Satchel", item: null },
      ],
      bags: [
        {
          name: "beltPouch",
          label: "Belt Pouch",
          maxBulk: 20,
          currentBulk: 10,
          items: [
            { name: "Healing Potion", material: "Glass", condition: 100, weight: 2, bulk: 1, noise: 0 },
            { name: "Keyring", material: "Steel", condition: 90, weight: 1, bulk: 1, noise: 0 },
          ],
        },
        {
          name: "satchel",
          label: "Satchel",
          maxBulk: 50,
          currentBulk: 25,
          items: [
            { name: "Spell Tome", material: "Paper", condition: 80, weight: 5, bulk: 3, noise: 1 },
            { name: "Gold Coins", material: "Metal", condition: 100, weight: 15, bulk: 20, noise: 5 },
          ],
        },
      ],
    };
  },
};
</script>

<style scoped>
/* Full layout for the inventory tab */
.inventory-layout {
  display: flex;
  gap: 20px;
  width: 100%;
}

/* Equipment Panel (Left) */
.equipment-panel {
  flex: 1;
  background: #1e1e1e;
  padding: 15px;
  border-radius: 5px;
}
.person-outline {
  display: grid;
  grid-template-areas:
    "head head"
    "torso torso"
    "mainHand offHand"
    "scabbard beltPouch"
    "legs legs"
    "feet feet";
  gap: 15px;
  grid-template-columns: 1fr 1fr;
}
.item-slot {
  padding: 10px;
  background: #333;
  border: 1px solid #444;
  border-radius: 5px;
  text-align: center;
}
.empty-slot {
  color: #777;
}
.slot-label {
  font-size: 0.9rem;
  margin-bottom: 5px;
  font-weight: bold;
}

/* Inventory Panel (Right) */
.inventory-panel {
  flex: 1.5;
  background: #1e1e1e;
  padding: 15px;
  border-radius: 5px;
}
.bag {
  margin-bottom: 20px;
}
.bag-header {
  font-size: 1.2rem;
  color: #ff9800;
  margin-bottom: 10px;
}
.bag-item {
  background: #333;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 5px;
}
.bag-item p {
  margin: 5px 0;
}
</style>