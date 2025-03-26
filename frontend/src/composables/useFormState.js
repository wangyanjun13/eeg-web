import { reactive, watch } from 'vue'

/**
 * 管理表单状态，支持持久化和重置
 * @param {string} storageKey 本地存储键名
 * @param {Object} initialState 初始状态
 * @param {Object} options 配置选项
 * @returns {Object} 表单状态和控制方法
 */
export function useFormState(storageKey, initialState = {}, options = {}) {
  const { 
    persist = true,  // 是否持久化到localStorage
    debounce = 500   // 持久化防抖时间
  } = options
  
  // 尝试从localStorage恢复状态
  let savedState = null
  if (persist) {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        savedState = JSON.parse(saved)
      }
    } catch (e) {
      console.error('Error restoring form state:', e)
    }
  }
  
  // 创建响应式表单状态
  const formState = reactive({ ...initialState, ...savedState })
  
  // 设置持久化
  if (persist) {
    let timeout
    watch(formState, () => {
      clearTimeout(timeout)
      timeout = setTimeout(() => {
        localStorage.setItem(storageKey, JSON.stringify(formState))
      }, debounce)
    }, { deep: true })
  }
  
  // 重置表单
  function resetForm(newState = initialState) {
    Object.keys(formState).forEach(key => {
      delete formState[key]
    })
    Object.assign(formState, newState)
  }
  
  // 清除持久化数据
  function clearSaved() {
    if (persist) {
      localStorage.removeItem(storageKey)
    }
  }
  
  return {
    formState,
    resetForm,
    clearSaved
  }
} 