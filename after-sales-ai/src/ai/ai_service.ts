/**
 * AI 服务：从后端知识库获取数据并匹配问题
 */
import type { Device, AIResponse } from '@/models/types'
import { searchKnowledgeArticles, type KnowledgeArticleDto } from '@/api/knowledge'

/**
 * 根据问题和设备信息生成 AI 回答
 */
export async function generateAIResponse(
  questionText: string,
  device: Device
): Promise<AIResponse & { relatedArticles?: Array<{ id: number; title: string; questionText?: string }> }> {
  console.log('开始搜索知识库，问题:', questionText)
  
  // 从后端搜索知识库
  // 暂时不限制status，先搜索所有状态的数据（后续可以优化）
  const searchResults = await searchKnowledgeArticles({
    keyword: questionText,
    // status: 'published', // 暂时移除，先搜索所有状态的数据
    pageIndex: 1,
    pageSize: 10 // 获取前10个结果，用于匹配和展示
  })

  console.log('搜索结果:', {
    totalCount: searchResults.totalCount,
    itemsCount: searchResults.items.length,
    items: searchResults.items.map(item => ({ id: item.id, title: item.title, status: item.status }))
  })

  if (searchResults.items.length === 0) {
    // 没有找到匹配的知识条目
    console.warn('未找到匹配的知识条目')
    return handleNoMatch(questionText, device)
  }

  // 找到匹配的知识条目，使用第一个（最相近的）作为主要回答
  const primaryArticle = searchResults.items[0]
  const relatedArticles = searchResults.items.slice(1) // 其他可能匹配的

  // 将知识条目转换为 AI 响应格式
  return convertArticleToAIResponse(primaryArticle, relatedArticles, questionText, device)
}

/**
 * 将知识条目转换为 AI 响应格式
 */
function convertArticleToAIResponse(
  article: KnowledgeArticleDto,
  relatedArticles: KnowledgeArticleDto[],
  questionText: string,
  device: Device
): AIResponse & { relatedArticles?: Array<{ id: number; title: string; questionText?: string }> } {
  // 解析解决方案文本
  const solutionText = article.solutionText || ''
  const causeText = article.causeText || ''
  
  // 尝试从标题或问题文本中提取报警码
  const alarmCodeMatch = (article.title + ' ' + (article.questionText || '')).match(/E\d{3}/i)
  const alarmCode = alarmCodeMatch ? alarmCodeMatch[0].toUpperCase() : undefined

  // 从标题或问题文本中提取问题分类
  let issueCategory = '其他'
  if (alarmCode) {
    issueCategory = '报警码'
  } else if (article.title.includes('送料') || article.title.includes('进料')) {
    issueCategory = '送料异常'
  } else if (article.title.includes('压力')) {
    issueCategory = '压力异常'
  } else if (article.title.includes('温度')) {
    issueCategory = '温度异常'
  } else {
    // 尝试从标签中提取分类
    const tags = article.tags?.split(',').map(t => t.trim()) || []
    if (tags.length > 0) {
      issueCategory = tags[0]
    }
  }

  // 解析可能原因（从原因文本中提取）
  const topCauses = parseCauses(causeText)

  // 解析排查步骤（从解决方案文本中提取）
  const steps = parseSteps(solutionText)

  // 解析临时和最终解决方案
  const solution = parseSolution(solutionText)

  // 计算置信度（基于匹配的知识条目数量和质量）
  let confidence = 0.8
  if (relatedArticles.length > 0) {
    // 如果有多个匹配项，说明问题描述可能不够精确
    confidence = 0.7
  }
  if (!alarmCode && topCauses.length === 0) {
    // 如果信息不完整，降低置信度
    confidence = 0.6
  }

  // 生成简短回答文本
  const shortAnswerText = generateShortAnswer(article, alarmCode, topCauses)

  return {
    issueCategory,
    alarmCode,
    confidence,
    topCauses,
    steps,
    solution,
    safetyTip: '⚠️ 安全提示：处理故障前请先断电，确保安全。涉及电气部件时，请由专业技术人员操作。',
    citedDocs: [{
      kbId: article.id.toString(),
      title: article.title,
      excerpt: article.questionText || article.title
    }],
    shouldEscalate: confidence < 0.7,
    shortAnswerText,
    relatedArticles: relatedArticles.length > 0 ? relatedArticles.map(a => ({
      id: a.id,
      title: a.title,
      questionText: a.questionText
    })) : undefined
  }
}

/**
 * 解析可能原因
 */
function parseCauses(causeText: string): string[] {
  if (!causeText) return []
  
  // 尝试按行或序号分割
  const lines = causeText.split(/\n|；|;|。/).filter(line => line.trim())
  
  // 提取原因（去除序号和标记）
  const causes = lines
    .map(line => line.replace(/^\d+[\.、]?\s*/, '').replace(/^[•·]\s*/, '').trim())
    .filter(line => line.length > 5) // 过滤太短的行
    
  return causes.slice(0, 5) // 最多返回5个原因
}

/**
 * 解析排查步骤
 */
function parseSteps(solutionText: string): AIResponse['steps'] {
  if (!solutionText) return []
  
  const steps: AIResponse['steps'] = []
  const lines = solutionText.split(/\n|；|;|。/).filter(line => line.trim())
  
  let currentStep: Partial<AIResponse['steps'][0]> | null = null
  
  for (const line of lines) {
    // 检测步骤标题（包含"检查"、"测试"、"校准"等关键词）
    if (line.match(/检查|测试|校准|清理|调整|更换|维修/)) {
      if (currentStep && currentStep.title) {
        steps.push({
          title: currentStep.title,
          action: currentStep.action || currentStep.title,
          expect: currentStep.expect || '完成检查',
          next: currentStep.next || '进行下一步'
        })
      }
      currentStep = {
        title: line.replace(/^\d+[\.、]?\s*/, '').replace(/^[•·]\s*/, '').trim(),
        action: '',
        expect: '',
        next: ''
      }
    } else if (currentStep) {
      // 填充步骤内容
      if (!currentStep.action) {
        currentStep.action = line.trim()
      } else if (!currentStep.expect) {
        currentStep.expect = line.trim()
      } else if (!currentStep.next) {
        currentStep.next = line.trim()
      }
    }
  }
  
  // 添加最后一个步骤
  if (currentStep && currentStep.title) {
    steps.push({
      title: currentStep.title,
      action: currentStep.action || currentStep.title,
      expect: currentStep.expect || '完成检查',
      next: currentStep.next || '进行下一步'
    })
  }
  
  // 如果没有解析出步骤，创建一个默认步骤
  if (steps.length === 0 && solutionText) {
    steps.push({
      title: '查看解决方案',
      action: solutionText.substring(0, 100),
      expect: '问题得到解决',
      next: '如问题未解决，请联系技术支持'
    })
  }
  
  return steps
}

/**
 * 解析解决方案
 */
function parseSolution(solutionText: string): { temporary: string; final: string } {
  if (!solutionText) {
    return {
      temporary: '暂无临时解决方案',
      final: '请查看详细排查步骤或联系技术支持'
    }
  }
  
  // 尝试分割临时和最终方案（查找"临时"、"最终"、"根因"等关键词）
  const tempMatch = solutionText.match(/临时[：:]\s*([^。]+)/)
  const finalMatch = solutionText.match(/(?:最终|根因|永久)[：:]\s*([^。]+)/)
  
  return {
    temporary: tempMatch ? tempMatch[1].trim() : solutionText.substring(0, 100),
    final: finalMatch ? finalMatch[1].trim() : solutionText
  }
}

/**
 * 生成简短回答文本
 */
function generateShortAnswer(
  article: KnowledgeArticleDto,
  alarmCode: string | undefined,
  topCauses: string[]
): string {
  if (alarmCode) {
    return `已识别报警码 ${alarmCode}。${topCauses[0] || '请按照排查步骤逐步检查'}.`
  }
  
  if (topCauses.length > 0) {
    return `${article.title}。${topCauses[0]}。建议按照排查步骤逐步检查。`
  }
  
  return `${article.title}。请查看详细排查步骤和解决方案。`
}

/**
 * 处理没有匹配的情况
 */
function handleNoMatch(questionText: string, device: Device): AIResponse {
  return {
    issueCategory: '其他',
    confidence: 0.3,
    topCauses: [
      '问题描述不够详细',
      '知识库中暂无相关解决方案'
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
    shortAnswerText: '问题描述不够详细，无法在知识库中找到匹配的解决方案。请补充：机型/报警码/现象/最近操作等信息，或直接转人工客服。'
  }
}
