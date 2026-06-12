import { ref } from 'vue'

const listeners = ref(new Map())

function on(event, handler) {
  if (!listeners.value.has(event)) {
    listeners.value.set(event, new Set())
  }
  listeners.value.get(event).add(handler)
}

function off(event, handler) {
  if (listeners.value.has(event)) {
    listeners.value.get(event).delete(handler)
  }
}

function emit(event, payload) {
  if (listeners.value.has(event)) {
    listeners.value.get(event).forEach(handler => handler(payload))
  }
}

export function useEventBus() {
  return { on, off, emit }
}
