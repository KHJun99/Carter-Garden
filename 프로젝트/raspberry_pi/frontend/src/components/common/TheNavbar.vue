<template>
  <nav>
    <router-link to="/">Home</router-link> |
    <router-link to="/products">Products</router-link> |
    <router-link to="/cart">Cart</router-link> |
    <router-link to="/guide">Guide</router-link>
  </nav>
</template>

<script setup>
</script>

<style scoped>
nav {
  padding: 30px;
  text-align: center;
}

nav a {
  font-weight: bold;
  color: var(--kiosk-green-900);
  text-decoration: none;
  margin: 0 10px;
}

nav a.router-link-exact-active {
  color: #42b983;
}
</style>
