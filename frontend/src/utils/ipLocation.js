export const getConfidenceType = (confidence) => {
  if (confidence >= 0.9) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
}

export const getConfidenceText = (confidence) => {
  if (confidence >= 0.9) return '高'
  if (confidence >= 0.6) return '中'
  return '低'
}

export const getConfidenceColor = (confidence) => {
  if (confidence >= 0.9) return '#67C23A'
  if (confidence >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

export const getInterfaceTypeTag = (isUplink) => {
  return isUplink ? { type: 'danger', text: '上联' } : { type: 'success', text: '接入' }
}

export const formatLastSeen = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
