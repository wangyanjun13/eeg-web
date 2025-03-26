import { ref } from 'vue'

/**
 * 管理加载状态的组合式函数
 * @param {Object|boolean} initialState 初始加载状态
 * @returns {Object} 加载状态和控制方法
 */
export function useLoading(initialState = false) {
  // 支持对象或布尔值作为初始状态
  const isLoading = ref(typeof initialState === 'object' ? { ...initialState } : initialState)

  /**
   * 设置加载状态
   * @param {string|null} key 状态键名，如果isLoading是对象
   * @param {boolean} value 状态值
   */
  function setLoading(key, value) {
    if (typeof isLoading.value === 'object' && key) {
      isLoading.value[key] = value
    } else {
      isLoading.value = value
    }
  }

  /**
   * 包装异步操作，自动处理加载状态
   * @param {Promise} promise 要执行的异步操作
   * @param {string|null} key 状态键名，如果isLoading是对象
   * @returns {Promise} 原始promise的结果
   */
  async function withLoading(promise, key = null) {
    setLoading(key, true)
    try {
      return await promise
    } finally {
      setLoading(key, false)
    }
  }

  return {
    isLoading,
    setLoading,
    withLoading
  }
} 