"""在写作技法库里检索。

    python3 scripts/find.py 具体 名词            # 关键词检索，给 gid + 标题 + 效果
    python3 scripts/find.py --gid G0123          # 打出整张卡（含示例和 AI 执行指令）
    python3 scripts/find.py --domain 对话        # 列出该主题域下所有卡（三层合并）
    python3 scripts/find.py --list               # 19 个主题域各自有多少张

多个关键词用空格分开，全部命中才算（AND）；关键词在标题里命中比在效果里命中排得靠前。
不带 --gid 时只输出摘要，正文请用 --gid 取，避免一次读进整份文件。
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(HERE, 'references')
CARDS = json.load(open(os.path.join(REF, 'manifest.json'), encoding='utf-8'))


def brief(c, tag=''):
    eff = c['effect'][:64] + ('…' if len(c['effect']) > 64 else '')
    return f"{tag}{c['gid']}  [{c['layer']}·{c['domain']}]  {c['title']}\n        {eff}"


def card_text(gid):
    hit = [c for c in CARDS if c['gid'].lower() == gid.lower()]
    if not hit:
        sys.exit(f"没有 {gid} 这张卡")
    c = hit[0]
    path = os.path.join(HERE, c['file'])
    txt = open(path, encoding='utf-8').read()
    m = re.search(r'<!--\s*' + re.escape(c['gid']) + r'\b.*?-->\s*\n(.*?)(?=\n<!--\s*G\d|\Z)',
                  txt, re.S)
    if not m:
        sys.exit(f"{c['gid']} 在 {c['file']} 里找不到：references/ 与 manifest.json 不同步")
    print(f"文件：{c['file']}\n")
    print(m.group(1).strip())


def rank(words, mode):
    """mode='and' 要求全部命中；mode='or' 命中任意一个即可。"""
    scored = []
    for c in CARDS:
        head = (c['title'] + ' ' + c['effect'] + ' ' + c['domain'] + ' ' + c['layer']).lower()
        full = head + ' ' + c.get('body', '').lower()
        hits = [w.lower() for w in words if w.lower() in full]
        if not hits or (mode == 'and' and len(hits) != len(words)):
            continue
        score = sum((3 if w.lower() in head else 1) for w in hits)
        score /= len(words) if mode == 'or' else 1
        score += 0.5 if c['n'] > 1 else 0
        scored.append((score, len(hits), c))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]['gid']))
    return scored


def search(raw):
    words = [w for a in raw for w in a.split()]     # 允许整句当一个参数传进来
    scored = rank(words, 'and')
    note = ''
    if not scored:
        scored = rank(words, 'or')
        note = '（没有全部命中的，以下是只命中部分关键词的）'
    if not scored:
        print('没命中。换个更小的动作词，或用 --domain 看某一主题域的全部卡片。')
        return
    print(f"命中 {len(scored)} 张{note}：\n")
    for s, h, c in scored[:25]:
        print(brief(c))
    if len(scored) > 25:
        print(f"\n…还有 {len(scored) - 25} 张，加关键词收窄。")


def domain(name):
    hit = [c for c in CARDS if name in c['domain']]
    if not hit:
        sys.exit('没有这个主题域。用 --list 看全部。')
    by = {}
    for c in hit:
        by.setdefault(c['layer'], []).append(c)
    print(f"主题域「{hit[0]['domain']}」共 {len(hit)} 张：\n")
    for layer in ['句子层', '段落/场景层', '叙事结构层']:
        if layer not in by:
            continue
        print(f"## {layer}（{len(by[layer])} 张）")
        for c in sorted(by[layer], key=lambda x: x['gid']):
            print(brief(c, '  '))
        print()


def listing():
    d = {}
    for c in CARDS:
        d.setdefault(c['domain'], {}).setdefault(c['layer'], 0)
        d[c['domain']][c['layer']] += 1
    print(f"{'主题域':<14}{'句子层':>6}{'段落场景层':>8}{'叙事结构层':>8}{'合计':>6}")
    for k, v in sorted(d.items(), key=lambda x: -sum(x[1].values())):
        s, p, n = v.get('句子层', 0), v.get('段落/场景层', 0), v.get('叙事结构层', 0)
        print(f"{k:<14}{s:>6}{p:>8}{n:>8}{s + p + n:>6}")
    print(f"{'合计':<14}{sum(1 for c in CARDS if c['layer'] == '句子层'):>6}"
          f"{sum(1 for c in CARDS if c['layer'] == '段落/场景层'):>8}"
          f"{sum(1 for c in CARDS if c['layer'] == '叙事结构层'):>8}{len(CARDS):>6}")


args = sys.argv[1:]
if not args:
    print(__doc__)
elif args[0] == '--gid':
    card_text(args[1])
elif args[0] == '--domain':
    domain(args[1])
elif args[0] == '--list':
    listing()
else:
    search(args)
