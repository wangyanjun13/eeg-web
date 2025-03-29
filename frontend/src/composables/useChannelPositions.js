import { ref, computed } from 'vue';
import datasetService from '@/services/dataset';

/**
 * 通道位置管理的组合式函数
 * @returns {Object} 通道位置相关的方法和数据
 */
export function useChannelPositions() {
  const customPositions = ref(null);
  const isLoading = ref(false);
  const error = ref(null);
  const positionSource = ref('none'); // 'set_file', 'none', 'error'
  
  /**
   * 从后端获取电极位置数据
   * @param {string} datasetId - 数据集ID
   * @param {string} subjectId - 受试者ID
   */
  const fetchElectrodePositions = async (datasetId, subjectId) => {
    if (!datasetId || !subjectId) return;
    
    isLoading.value = true;
    error.value = null;
    
    try {
      const response = await datasetService.getElectrodePositions(datasetId, subjectId);
      
      if (response.data && response.data.positions && Object.keys(response.data.positions).length > 0) {
        customPositions.value = response.data.positions;
        positionSource.value = response.data.source;
      } else {
        customPositions.value = null;
        positionSource.value = response.data.source || 'none';
      }
    } catch (err) {
      console.error('获取电极位置失败:', err);
      error.value = err.message || '获取电极位置失败';
      positionSource.value = 'error';
    } finally {
      isLoading.value = false;
    }
  };
  
  /**
   * 重置位置数据
   */
  const resetPositions = () => {
    customPositions.value = null;
    positionSource.value = 'none';
  };
  
  /**
   * 获取通道位置
   * @param {string} channel - 通道名称
   * @param {number} index - 通道索引
   * @param {number} total - 通道总数
   * @returns {Object} 包含x和y坐标的对象
   */
  const getChannelPosition = (channel, index, total) => {
    // 如果有自定义位置，则使用自定义位置的x和y坐标
    if (customPositions.value && customPositions.value[channel]) {
      const pos = customPositions.value[channel];
      
      // 计算头部中心点
      const centerX = 0.5;
      const centerY = 0.5;
      
      // 使用更大的缩放因子，确保电极位置分散
      const scaleFactor = 3.5; // 增大缩放因子，使电极分布更广
      
      // 计算最终位置 - 简化坐标转换
      return { 
        x: centerX - pos.x * scaleFactor,
        y: centerY - pos.y * scaleFactor
      };
    }
    
    // 如果没有预定义位置，则在头部轮廓内均匀分布
    // 使用极坐标系统来分布通道
    const radius = 0.4; // 头部半径
    const angle = (index / total) * 2 * Math.PI;
    const x = 0.5 + radius * Math.cos(angle);
    const y = 0.5 + radius * Math.sin(angle);
    
    return { x, y };
  };
  
  return {
    fetchElectrodePositions,
    resetPositions,
    getChannelPosition,
    isLoading,
    error,
    positionSource,
    hasCustomPositions: computed(() => !!customPositions.value)
  };
} 