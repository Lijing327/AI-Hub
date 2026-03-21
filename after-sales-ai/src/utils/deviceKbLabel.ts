/**
 * 根据设备型号/展示名推断知识库分类名（与 Python device_type_utils 前缀与关键词对齐，仅用于前端展示）
 */
export function deviceCategoryLabelFromModel(model: string | undefined | null): string {
  if (!model || !String(model).trim()) {
    return '智能客服'
  }
  const m = String(model).trim()
  const low = m.toLowerCase()
  if (low.includes('抛丸') || low.includes('抛瓦') || low.includes('喷砂') || /^pw/i.test(m) || low.includes(' pw')) {
    return '抛丸机'
  }
  if (low.includes('浇注') || low.includes('保温炉') || /^jz/i.test(m) || low.includes(' jz')) {
    return '浇注机'
  }
  if (low.includes('造型') || low.includes('射砂') || /^yh/i.test(m) || low.includes(' yh')) {
    return '造型机'
  }
  return m
}

/** 说明发送聊天时会带给后端的 device_model（便于用户确认「真的切设备了」） */
export function deviceModelForApiHint(model: string | undefined | null): string {
  if (!model || !String(model).trim()) {
    return ''
  }
  return String(model).trim()
}
