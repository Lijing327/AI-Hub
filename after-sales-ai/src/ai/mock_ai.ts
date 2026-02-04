/**
 * Mock AI 服务：模拟 AI 回答生成
 */

import type { Device, AIResponse, KbSample } from '@/models/types'
import kbSamples from '@/mock/kb_samples.json'

/**
 * 根据问题和设备信息生成 AI 回答
 */
export async function generateAIResponse(
  questionText: string,
  device: Device
): Promise<AIResponse> {
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 700))

  const question = questionText.toLowerCase()
  const alarmCodeMatch = question.match(/e\d{3}/i)

  // 匹配报警码
  if (alarmCodeMatch) {
    const alarmCode = alarmCodeMatch[0].toUpperCase()
    return handleAlarmCode(alarmCode, device)
  }

  // 匹配送料异常
  if (question.includes('送料') || question.includes('不进料') || question.includes('卡料')) {
    return handleFeedingIssue(device)
  }

  // 匹配压力异常
  if (question.includes('压力') || question.includes('不稳') || question.includes('波动')) {
    return handlePressureIssue(device)
  }

  // 匹配温度异常
  if (question.includes('温度') || question.includes('过热') || question.includes('高温')) {
    return handleTemperatureIssue(device)
  }

  // 默认：信息不足
  return handleInsufficientInfo(device)
}

/**
 * 处理报警码问题
 */
function handleAlarmCode(alarmCode: string, _device: Device): AIResponse {
  const kb = kbSamples as KbSample[]
  let category = '报警码'
  let confidence = 0.85
  let topCauses: string[] = []
  let steps: AIResponse['steps'] = []
  let solution = { temporary: '', final: '' }
  let citedDocs: AIResponse['citedDocs'] = []

  switch (alarmCode) {
    case 'E101':
      category = '报警码'
      topCauses = [
        '温度传感器连接线松动或断裂',
        '温度传感器本身故障',
        '控制器接口接触不良'
      ]
      steps = [
        {
          title: '检查传感器连接',
          action: '检查温度传感器连接线是否松动，重新插拔连接器',
          expect: '连接线牢固，无松动',
          next: '如连接正常，进行下一步'
        },
        {
          title: '测量传感器阻值',
          action: '使用万用表测量温度传感器阻值，对比标准值',
          expect: '阻值在正常范围内（通常 100Ω-1000Ω）',
          next: '如阻值异常，更换传感器'
        },
        {
          title: '检查控制器接口',
          action: '检查控制器温度传感器接口是否有氧化或接触不良',
          expect: '接口清洁，接触良好',
          next: '如接口异常，清洁或更换接口'
        }
      ]
      solution = {
        temporary: '重启设备，检查温度传感器连接',
        final: '更换故障的温度传感器，确保连接牢固'
      }
      citedDocs = kb.filter((k) => k.kbId === 'kb_001').map((k) => ({
        kbId: k.kbId,
        title: k.title,
        excerpt: k.excerpt
      }))
      break

    case 'E205':
      category = '报警码'
      topCauses = [
        '送料电机故障',
        '送料通道堵塞',
        '送料传感器异常',
        '送料参数设置不当'
      ]
      steps = [
        {
          title: '检查送料电机',
          action: '观察送料电机是否正常运转，听声音判断',
          expect: '电机运转平稳，无异常声音',
          next: '如电机异常，检查电机电源和驱动'
        },
        {
          title: '清理送料通道',
          action: '检查并清理送料通道，移除异物',
          expect: '通道畅通，无堵塞',
          next: '如通道正常，检查传感器'
        },
        {
          title: '校准送料传感器',
          action: '检查送料传感器是否被遮挡，校准传感器位置',
          expect: '传感器工作正常，信号稳定',
          next: '如传感器正常，检查参数设置'
        },
        {
          title: '调整送料参数',
          action: '检查送料速度、压力、时间等参数设置',
          expect: '参数设置合理，符合工艺要求',
          next: '如参数异常，调整后重新测试'
        }
      ]
      solution = {
        temporary: '清理送料通道，重启送料系统',
        final: '根据具体原因修复：更换电机/清理通道/校准传感器/调整参数'
      }
      citedDocs = kb.filter((k) => k.kbId === 'kb_002' || k.kbId === 'kb_004').map((k) => ({
        kbId: k.kbId,
        title: k.title,
        excerpt: k.excerpt
      }))
      break

    case 'E308':
      category = '报警码'
      topCauses = [
        '压力传感器故障',
        '压力管路泄漏',
        '压力泵异常',
        '压力调节阀卡滞'
      ]
      steps = [
        {
          title: '检查压力传感器',
          action: '观察压力传感器读数，检查传感器连接',
          expect: '传感器读数稳定，连接正常',
          next: '如传感器异常，更换传感器'
        },
        {
          title: '检查管路密封',
          action: '检查压力管路是否有泄漏，听声音判断',
          expect: '管路无泄漏，密封良好',
          next: '如有泄漏，修复密封'
        },
        {
          title: '测试压力泵',
          action: '测试压力泵输出是否正常',
          expect: '压力泵输出稳定，符合设定值',
          next: '如压力泵异常，检查泵体或更换'
        },
        {
          title: '检查调节阀',
          action: '检查压力调节阀动作是否正常，清洁阀体',
          expect: '调节阀动作灵活，无卡滞',
          next: '如调节阀异常，清洁或更换'
        }
      ]
      solution = {
        temporary: '检查压力系统，临时调整压力设定值',
        final: '根据具体原因修复：更换传感器/修复泄漏/维修压力泵/清洁调节阀'
      }
      citedDocs = kb.filter((k) => k.kbId === 'kb_003' || k.kbId === 'kb_005').map((k) => ({
        kbId: k.kbId,
        title: k.title,
        excerpt: k.excerpt
      }))
      break

    default:
      confidence = 0.6
      topCauses = ['报警码未识别，需要进一步排查']
      steps = [
        {
          title: '记录报警信息',
          action: '记录完整的报警码、报警时间、设备状态',
          expect: '信息记录完整',
          next: '联系技术支持'
        }
      ]
      solution = {
        temporary: '记录报警信息，观察设备运行状态',
        final: '联系技术支持，提供详细报警信息'
      }
  }

  return {
    issueCategory: category,
    alarmCode,
    confidence,
    topCauses,
    steps,
    solution,
    safetyTip: '⚠️ 安全提示：处理故障前请先断电，确保安全。涉及电气部件时，请由专业技术人员操作。',
    citedDocs,
    shouldEscalate: confidence < 0.7,
    shortAnswerText: `已识别报警码 ${alarmCode}。${topCauses[0]}。建议按照排查步骤逐步检查。`
  }
}

/**
 * 处理送料异常
 */
function handleFeedingIssue(_device: Device): AIResponse {
  const kb = kbSamples as KbSample[]
  const citedDocs = kb.filter((k) => k.kbId === 'kb_004').map((k) => ({
    kbId: k.kbId,
    title: k.title,
    excerpt: k.excerpt
  }))

  return {
    issueCategory: '送料异常',
    confidence: 0.8,
    topCauses: [
      '送料电机故障或电源异常',
      '送料通道被异物堵塞',
      '送料传感器被遮挡或故障',
      '送料参数设置不当（速度/压力/时间）'
    ],
    steps: [
      {
        title: '检查送料电机',
        action: '观察送料电机是否正常运转，检查电机电源和驱动',
        expect: '电机运转正常，无异常声音',
        next: '如电机异常，检查电源和驱动电路'
      },
      {
        title: '清理送料通道',
        action: '检查送料通道是否有异物堵塞，清理通道',
        expect: '通道畅通，无堵塞物',
        next: '如通道正常，检查传感器'
      },
      {
        title: '检查送料传感器',
        action: '检查送料传感器是否被遮挡，测试传感器信号',
        expect: '传感器工作正常，信号稳定',
        next: '如传感器异常，清洁或更换传感器'
      },
      {
        title: '检查送料参数',
        action: '检查送料速度、压力、时间等参数设置是否合理',
        expect: '参数设置符合工艺要求',
        next: '如参数异常，调整后重新测试'
      }
    ],
    solution: {
      temporary: '清理送料通道，重启送料系统，临时调整送料速度',
      final: '根据具体原因修复：更换电机/清理通道/校准传感器/调整参数。如送料机构磨损，需更换相关部件。'
    },
    safetyTip: '⚠️ 安全提示：清理送料通道前请先断电，确保设备完全停止。注意不要用手直接接触送料机构。',
    citedDocs,
    shouldEscalate: false,
    shortAnswerText: '送料异常通常由电机故障、通道堵塞、传感器异常或参数设置不当引起。建议按照排查步骤逐步检查。'
  }
}

/**
 * 处理压力异常
 */
function handlePressureIssue(_device: Device): AIResponse {
  const kb = kbSamples as KbSample[]
  const citedDocs = kb.filter((k) => k.kbId === 'kb_005').map((k) => ({
    kbId: k.kbId,
    title: k.title,
    excerpt: k.excerpt
  }))

  return {
    issueCategory: '压力异常',
    confidence: 0.75,
    topCauses: [
      '压力传感器漂移或故障',
      '压力管路有气泡或泄漏',
      '压力泵性能下降',
      '压力调节阀响应慢或卡滞'
    ],
    steps: [
      {
        title: '校准压力传感器',
        action: '检查压力传感器读数，对比标准值，必要时校准',
        expect: '传感器读数准确，无漂移',
        next: '如传感器异常，更换传感器'
      },
      {
        title: '排气处理',
        action: '检查压力管路是否有气泡，进行排气处理',
        expect: '管路无气泡，压力稳定',
        next: '如仍有问题，检查泄漏'
      },
      {
        title: '检查压力泵',
        action: '测试压力泵输出性能，检查泵体是否正常',
        expect: '压力泵输出稳定，符合设定值',
        next: '如压力泵异常，维修或更换'
      },
      {
        title: '清洁调节阀',
        action: '检查压力调节阀动作，清洁阀体',
        expect: '调节阀动作灵活，响应及时',
        next: '如调节阀异常，清洁或更换'
      }
    ],
    solution: {
      temporary: '临时调整压力设定值，进行排气处理',
      final: '根据具体原因修复：校准/更换传感器、修复泄漏、维修压力泵、清洁调节阀。检查所有密封件。'
    },
    safetyTip: '⚠️ 安全提示：检查压力系统前请先泄压，确保安全。高压操作需由专业技术人员进行。',
    citedDocs,
    shouldEscalate: false,
    shortAnswerText: '压力不稳通常由传感器漂移、管路气泡/泄漏、压力泵异常或调节阀卡滞引起。建议按照排查步骤逐步检查。'
  }
}

/**
 * 处理温度异常
 */
function handleTemperatureIssue(_device: Device): AIResponse {
  const kb = kbSamples as KbSample[]
  const citedDocs = kb.filter((k) => k.kbId === 'kb_006').map((k) => ({
    kbId: k.kbId,
    title: k.title,
    excerpt: k.excerpt
  }))

  return {
    issueCategory: '温度异常',
    confidence: 0.8,
    topCauses: [
      '冷却系统故障（风扇/冷却水）',
      '环境温度过高',
      '加热系统失控',
      '温度传感器误报'
    ],
    steps: [
      {
        title: '检查冷却系统',
        action: '检查冷却风扇是否运转，冷却水循环是否正常',
        expect: '冷却系统工作正常',
        next: '如冷却系统异常，修复或更换'
      },
      {
        title: '改善通风环境',
        action: '检查设备周围通风情况，确保散热良好',
        expect: '通风良好，环境温度正常',
        next: '如环境温度过高，改善通风'
      },
      {
        title: '检查加热系统',
        action: '检查加热器控制电路，测试加热器工作状态',
        expect: '加热系统控制正常，无失控',
        next: '如加热系统异常，检查控制电路'
      },
      {
        title: '校准温度传感器',
        action: '检查温度传感器读数，对比标准值，必要时校准',
        expect: '传感器读数准确',
        next: '如传感器异常，更换传感器'
      }
    ],
    solution: {
      temporary: '临时改善通风，检查冷却系统，降低设备负载',
      final: '根据具体原因修复：修复冷却系统、改善通风、修复加热控制、校准/更换传感器。'
    },
    safetyTip: '⚠️ 安全提示：检查温度系统时注意高温部件，避免烫伤。处理前请先断电，待设备冷却。',
    citedDocs,
    shouldEscalate: false,
    shortAnswerText: '温度过高通常由冷却系统故障、环境温度过高、加热系统失控或传感器误报引起。建议按照排查步骤逐步检查。'
  }
}

/**
 * 处理信息不足的情况
 */
function handleInsufficientInfo(_device: Device): AIResponse {
  return {
    issueCategory: '其他',
    confidence: 0.3,
    topCauses: [
      '问题描述不够详细',
      '缺少关键信息（报警码/现象/操作）'
    ],
    steps: [
      {
        title: '补充问题信息',
        action: '请提供以下信息：1) 设备型号和控制器版本；2) 报警码（如有）；3) 具体现象描述；4) 最近的操作',
        expect: '信息完整，便于诊断',
        next: '根据补充信息重新分析'
      }
    ],
    solution: {
      temporary: '暂时无法提供具体解决方案，需要更多信息',
      final: '请补充详细信息后重新咨询，或联系技术支持'
    },
    safetyTip: '⚠️ 安全提示：如设备出现异常，请先停止运行，确保安全。',
    citedDocs: [],
    shouldEscalate: true,
    shortAnswerText: '问题描述不够详细，无法准确诊断。请补充：机型/报警码/现象/最近操作等信息，或直接转人工客服。'
  }
}
