/**
 * 日期格式化工具函数
 */

/**
 * 格式化日期
 * @param {string|Date} date - 要格式化的日期
 * @param {string} format - 可选的格式模板，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return '-';
    
    try {
      let d;
      
      // 处理特殊格式的时间戳 "YYYYMMDDHHmmss"
      if (typeof date === 'string' && date.length === 14 && !isNaN(date)) {
        const year = date.substring(0, 4);
        const month = date.substring(4, 6);
        const day = date.substring(6, 8);
        const hours = date.substring(8, 10);
        const minutes = date.substring(10, 12);
        const seconds = date.substring(12, 14);
        
        d = new Date(`${year}-${month}-${day}T${hours}:${minutes}:${seconds}`);
      } else {
        d = typeof date === 'string' ? new Date(date) : date;
      }
      
      if (isNaN(d.getTime())) {
        console.warn('无效的日期格式:', date);
        return '-';
      }
      
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const hours = String(d.getHours()).padStart(2, '0');
      const minutes = String(d.getMinutes()).padStart(2, '0');
      const seconds = String(d.getSeconds()).padStart(2, '0');
      
      return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
    } catch (error) {
      console.error('日期格式化错误:', error, '日期值:', date);
      return '-';
    }
  }
  
  /**
   * 格式化文件大小
   * @param {number} size - 文件大小（字节）
   * @returns {string} 格式化后的文件大小字符串
   */
  export function formatFileSize(size) {
    if (!size && size !== 0) return '未知';
    
    const KB = 1024;
    const MB = KB * 1024;
    const GB = MB * 1024;
    
    if (size < KB) {
      return size + ' B';
    } else if (size < MB) {
      return (size / KB).toFixed(2) + ' KB';
    } else if (size < GB) {
      return (size / MB).toFixed(2) + ' MB';
    } else {
      return (size / GB).toFixed(2) + ' GB';
    }
  } 