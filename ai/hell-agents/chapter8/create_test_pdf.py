#!/usr/bin/env python3
"""创建测试PDF文件"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 创建PDF
pdf_file = "/tmp/test_ai_doc.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=letter)
styles = getSampleStyleSheet()
story = []

# 自定义样式
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=18,
    textColor='#2E4053',
    spaceAfter=30,
    alignment=1  # 居中
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=11,
    leading=16,
    spaceAfter=12,
    alignment=TA_JUSTIFY
)

# 添加内容
title = Paragraph("人工智能与机器学习基础", title_style)
story.append(title)
story.append(Spacer(1, 0.3*inch))

# 第一章
story.append(Paragraph("第一章：什么是机器学习？", styles['Heading2']))
story.append(Spacer(1, 0.2*inch))

content1 = """
机器学习（Machine Learning）是人工智能的一个重要分支。它的核心思想是让计算机系统能够从数据中自动学习和改进，而无需明确地编程。

在传统编程中，程序员需要编写详细的规则来处理各种情况。而在机器学习中，我们提供大量的数据给算法，让它自己发现数据中的模式和规律。

机器学习主要分为三类：
<strong>监督学习</strong>：使用带标签的数据进行训练，如图像分类、语音识别等。
<strong>无监督学习</strong>：使用无标签的数据，让算法自己发现数据结构，如聚类分析。
<strong>强化学习</strong>：通过与环境交互获得奖励或惩罚来学习，如游戏AI、机器人控制。
"""

story.append(Paragraph(content1, body_style))
story.append(Spacer(1, 0.3*inch))

# 第二章
story.append(Paragraph("第二章：神经网络基础", styles['Heading2']))
story.append(Spacer(1, 0.2*inch))

content2 = """
神经网络（Neural Network）是一种受人脑神经元结构启发的计算模型。它由大量相互连接的节点（神经元）组成，这些节点组织成层次结构。

<strong>输入层</strong>：接收原始数据，如图像的像素值或文本的特征向量。
<strong>隐藏层</strong>：进行特征提取和模式识别，可以有多层，形成"深度"神经网络。
<strong>输出层</strong>：产生最终的预测或分类结果。

每个连接都有一个权重，表示信号的重要性。网络通过调整这些权重来学习，这个过程称为"训练"或"学习"。

深度学习（Deep Learning）就是使用多层神经网络的技术，它在图像识别、自然语言处理等领域取得了突破性进展。
"""

story.append(Paragraph(content2, body_style))
story.append(Spacer(1, 0.3*inch))

# 第三章
story.append(Paragraph("第三章：Transformer架构", styles['Heading2']))
story.append(Spacer(1, 0.2*inch))

content3 = """
Transformer是2017年提出的一种革命性神经网络架构，它彻底改变了自然语言处理领域。

Transformer的核心创新是<strong>自注意力机制（Self-Attention）</strong>。传统RNN需要按顺序处理文本，而Transformer可以同时处理整个序列，大大提高了并行计算效率。

自注意力机制让模型能够关注输入序列中的重要部分。例如，在处理"苹果公司发布了新产品"时，当模型关注"苹果"这个词时，注意力机制会帮助它理解这里的"苹果"指的是公司而不是水果。

基于Transformer的模型包括：
<strong>BERT</strong>：双向编码器表示，用于理解和分类文本。
<strong>GPT</strong>：生成式预训练Transformer，用于文本生成。
<strong>T5</strong>：文本到文本转换Transformer。

这些模型在各种NLP任务上取得了state-of-the-art的性能。
"""

story.append(Paragraph(content3, body_style))
story.append(Spacer(1, 0.3*inch))

# 第四章
story.append(Paragraph("第四章：大语言模型", styles['Heading2']))
story.append(Spacer(1, 0.2*inch))

content4 = """
大语言模型（Large Language Models，简称LLMs）是近年来AI领域最重要的突破之一。这些模型在互联网规模的海量文本数据上进行训练，学习到了丰富的语言知识和世界知识。

LLMs的特点包括：
<strong>涌现能力</strong>：随着模型规模增大，一些能力会突然出现，如上下文学习、推理能力等。
<strong>通用性</strong>：一个模型可以处理多种任务，无需专门训练。
<strong>规模效应</strong>：性能随着模型规模、数据量和计算资源的增加而持续提升。

著名的LLMs包括GPT系列、BERT、LLaMA、Claude等。这些模型不仅能够理解和生成自然语言，还能进行数学计算、代码生成、创意写作等复杂任务。

然而，LLMs也面临挑战，如幻觉问题（生成不正确信息）、偏见问题、计算成本高昂等。研究人员正在积极解决这些问题。
"""

story.append(Paragraph(content4, body_style))
story.append(Spacer(1, 0.3*inch))

# 总结
story.append(Paragraph("总结", styles['Heading2']))
story.append(Spacer(1, 0.2*inch))

content5 = """
人工智能和机器学习正在快速发展，从早期的规则系统到今天的深度学习和大语言模型，我们见证了技术的巨大进步。

未来，AI系统将变得更加智能、更加可靠、更加有用。但同时也需要我们谨慎思考其伦理影响和社会影响，确保AI技术的发展造福人类。

学习AI技术需要：
1. 扎实的数学基础（线性代数、概率统计）
2. 编程技能（Python是最流行的语言）
3. 持续学习的心态（技术发展迅速）
4. 实践项目经验（理论和实践相结合）

希望这份文档能帮助你开始AI学习之旅！
"""

story.append(Paragraph(content5, body_style))

# 生成PDF
doc.build(story)
print(f"✅ 测试PDF已创建: {pdf_file}")
print(f"📄 主题：人工智能与机器学习基础")
print(f"📊 内容：5个章节，约1500字")
