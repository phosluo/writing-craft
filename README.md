# writing-craft

写作技法库，一个 [Claude Code](https://claude.com/claude-code) skill。

916 张可执行卡片，从 9 本英文写作书里提炼。每张卡不是一句道理，而是一个动作：给你结构公式、书里的英文原句（逐字摘录 + 中文点破）、可以直接照做的 AI 执行指令。

## 安装

放进 skills 目录即可，Claude Code 自动发现：

```bash
git clone git@github.com:phosluo/writing-craft.git ~/.claude/skills/writing-craft
```

## 用

```bash
# 关键词检索，给 gid + 标题 + 一句话效果
python3 ~/.claude/skills/writing-craft/scripts/find.py 具体 名词

# 取整张卡：公式、例句、点破、变体、反模式、AI 执行指令
python3 ~/.claude/skills/writing-craft/scripts/find.py --gid G0860

# 看某个主题域下三层的全部卡片
python3 ~/.claude/skills/writing-craft/scripts/find.py --domain 对话

# 19 个主题域各有多少张
python3 ~/.claude/skills/writing-craft/scripts/find.py --list
```

检索词用**动作词**（具体、删除、延迟、并置），别用「生动」「高级」这类感觉词。

## 结构

```
SKILL.md            入口：三层怎么判断、一张卡怎么读、改稿流程、硬规则
references/
  00-索引.md        916 张卡的标题索引（★ 多书合并 / · 单书来源）
  manifest.json     检索清单，find.py 读它
  句子层/ 段落场景层/ 叙事结构层/     按主题域分的 74 个卡片文件
scripts/
  find.py           检索与取卡
```

卡片按「层 → 主题域」组织。层决定你在哪一级动手：

| 层 | 管什么 |
|---|---|
| 句子层（312 张） | 一个句子内部的选词、语序、节奏、标点 |
| 段落/场景层（294 张） | 一个段落或场景内部的组织、推进、描写、对话 |
| 叙事结构层（310 张） | 全篇的视角、时间、悬念、伏笔、开头结尾、主题 |

## 数据

- 916 张成品卡，来自 1,354 张提取出来的来源卡，一张没丢
- 270 张是多本书都讲到的同一条原则合并而成
- 2,697 条英文例句全部逐字核对过原书语料，每条配中文点破
- 19 个主题域，来源 9 本英文写作书（Storycraft、The Art of X-Ray Reading、100 Ways to Improve Your Writing、Several Short Sentences About Writing、Sin and Syntax、Techniques of the Selling Writer 等）
