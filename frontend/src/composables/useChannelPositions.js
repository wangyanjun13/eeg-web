import { ref, computed, h } from 'vue';
import datasetService from '@/services/dataset';
import { ElMessage, ElDialog, ElButton, ElCheckboxGroup, ElCheckbox } from 'element-plus';

/**
 * 通道位置管理的组合式函数
 * @returns {Object} 通道位置相关的方法和数据
 */
export function useChannelPositions() {
  const customPositions = ref(null);
  const isLoading = ref(false);
  const error = ref(null);
  const positionSource = ref('none'); // 'set_file', 'none', 'error'
  
  // 通道选择对话框状态
  const channelSelectVisible = ref(false);
  const localSelectedChannels = ref([]);
  
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
      const scaleFactor = 4.0; // 增大缩放因子，进一步分散电极
      
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
  
  // 通道选择相关方法
  const openChannelSelect = (currentChannels, allChannels, onConfirm) => {
    localSelectedChannels.value = [...currentChannels];
    channelSelectVisible.value = true;
    
    // 保存回调和数据
    openChannelSelect._callback = onConfirm;
    openChannelSelect._allChannels = allChannels;
  };
  
  const isSelectAll = computed(() => {
    const allChannels = openChannelSelect._allChannels || [];
    return allChannels.length > 0 && localSelectedChannels.value.length === allChannels.length;
  });
  
  const toggleSelectAll = () => {
    const allChannels = openChannelSelect._allChannels || [];
    localSelectedChannels.value = isSelectAll.value ? [] : [...allChannels];
  };
  
  const confirmChannelSelect = () => {
    if (localSelectedChannels.value.length === 0) {
      ElMessage.warning('请至少选择一个通道');
      return;
    }
    
    channelSelectVisible.value = false;
    if (openChannelSelect._callback) {
      openChannelSelect._callback([...localSelectedChannels.value]);
    }
  };
  
  const cancelChannelSelect = () => {
    channelSelectVisible.value = false;
  };
  
  const toggleChannel = (channel) => {
    const index = localSelectedChannels.value.indexOf(channel);
    if (index > -1) {
      localSelectedChannels.value.splice(index, 1);
    } else {
      localSelectedChannels.value.push(channel);
    }
  };
  
  // 渲染通道选择对话框
  const renderChannelSelectDialog = () => {
    const allChannels = openChannelSelect._allChannels || [];
    
    return h(ElDialog, {
      modelValue: channelSelectVisible.value,
      'onUpdate:modelValue': (val) => channelSelectVisible.value = val,
      title: '选择要显示的通道',
      width: '60%',
      customClass: 'channel-select-dialog'
    }, {
      default: () => [
        h('div', { class: 'channel-select-header' }, [
          h(ElButton, {
            size: 'small',
            type: 'primary',
            onClick: toggleSelectAll
          }, () => isSelectAll.value ? '清空' : '全选'),
          
          h('div', { class: 'selected-count' }, 
            `已选通道: ${localSelectedChannels.value.length}/${allChannels.length || 0}`)
        ]),
        
        positionSource.value !== 'none' 
          ? h('div', { class: 'head-container' }, [
              h('div', { class: 'head-circle' }),
              h('div', { class: 'ear left-ear' }),
              h('div', { class: 'ear right-ear' }),
              h('div', { class: 'nose' }),
              
              ...allChannels.map((channel, index) => 
                h('div', {
                  key: channel,
                  class: ['channel-marker', { 'selected': localSelectedChannels.value.includes(channel) }],
                  style: {
                    left: `${getChannelPosition(channel, index, allChannels.length).x * 100}%`,
                    top: `${getChannelPosition(channel, index, allChannels.length).y * 100}%`
                  },
                  onClick: () => toggleChannel(channel)
                }, [
                  h('span', { class: 'channel-label' }, channel)
                ])
              )
            ])
          : h(ElCheckboxGroup, {
              modelValue: localSelectedChannels.value,
              'onUpdate:modelValue': (val) => localSelectedChannels.value = val,
              class: 'channel-grid'
            }, () => 
              allChannels.map(channel => 
                h(ElCheckbox, { key: channel, label: channel }, () => channel)
              )
            )
      ],
      footer: () => h('span', { class: 'dialog-footer' }, [
        h(ElButton, { onClick: cancelChannelSelect }, () => '取消'),
        h(ElButton, { type: 'primary', onClick: confirmChannelSelect }, () => '确认')
      ])
    });
  };
  
  return {
    fetchElectrodePositions,
    resetPositions,
    getChannelPosition,
    isLoading,
    error,
    positionSource,
    hasCustomPositions: computed(() => !!customPositions.value),
    // 通道选择相关
    channelSelectVisible,
    localSelectedChannels,
    openChannelSelect,
    toggleSelectAll,
    confirmChannelSelect,
    cancelChannelSelect,
    toggleChannel,
    renderChannelSelectDialog,
    isSelectAll
  };
} 