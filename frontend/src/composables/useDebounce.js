import { customRef } from 'vue'

/**
 * 创建一个防抖值
 * @param {any} initialValue 初始值
 * @param {number} delay 延迟时间（毫秒）
 * @returns {Ref} 防抖后的响应式值
 */
export function useDebounce(initialValue, delay = 300) {
  return customRef((track, trigger) => {
    let timeout
    let value = initialValue
    
    return {
      get() {
        track()
        return value
      },
      set(newValue) {
        clearTimeout(timeout)
        timeout = setTimeout(() => {
          value = newValue
          trigger()
        }, delay)
      }
    }
  })
}

/**
 * 创建一个防抖函数
 * @param {Function} fn 要防抖的函数
 * @param {number} delay 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function useDebounceFn(fn, delay = 300) {
  let timeout = null
  
  function debounced(...args) {
    clearTimeout(timeout)
    
    return new Promise((resolve) => {
      timeout = setTimeout(() => {
        resolve(fn(...args))
      }, delay)
    })
  }
  
  return debounced
} 