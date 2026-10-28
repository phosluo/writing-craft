"""在写作技法库里检索。

    python3 scripts/find.py 具体 名词              # 关键词检索，给 gid + 标题 + 效果
    python3 scripts/find.py --strict 声音 交叉      # 只在标题+效果+主题域里找，不回退、不放宽
    python3 scripts/find.py --layer 结构 悬念       # 限定一层：句子 / 段落 / 结构
    python3 scripts/find.py --top 10 具体           # 只看前 N 条（默认 25）
    python3 scripts/find.py --gid G0123            # 打出整张卡（含示例和 AI 执行指令）
    python3 scripts/find.py --domain 对话          # 列出该主题域下所有卡（三层合并）
    python3 scripts/find.py --list                 # 19 个主题域各自有多少张
    python3 scripts/find.py --verify 原文.txt 引文.md   # 核对引文是否逐字来自原文

多个关键词用空格分开，默认全部命中才算（AND）；一条都没全命中时自动退回宽松匹配，
并在结果里标明哪些卡只命中了部分词。加了 --strict 就不再有这个回退。
英文技法词会自动展开成库里用的中文说法（词表在 scripts/aliases.json）。
不带 --gid 时只输出摘要，正文请用 --gid 取，避免一次读进整份文件。
"""

import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(HERE, 'references')
CARDS = json.load(open(os.path.join(REF, 'manifest.json'), encoding='utf-8'))

ALIAS_PATH = os.path.join(HERE, 'scripts', 'aliases.json')
ALIAS = {}
if os.path.exists(ALIAS_PATH):
    ALIAS = {k.lower(): v for k, v in
             json.load(open(ALIAS_PATH, encoding='utf-8')).items()
             if not k.startswith('_')}

LAYERS = ['句子层', '段落/场景层', '叙事结构层']
LAYER_SHORT = {'句子': '句子层', '句': '句子层',
               '段落': '段落/场景层', '场景': '段落/场景层', '段': '段落/场景层',
               '结构': '叙事结构层', '叙事': '叙事结构层'}


def brief(c, tag='', partial=''):
    eff = c['effect'][:64] + ('…' if len(c['effect']) > 64 else '')
    return (f"{tag}{c['gid']}  [{c['layer']}·{c['domain']}]{partial}  {c['title']}\n"
            f"        {eff}")


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


def norm_layer(s):
    s = s.strip()
    if s in LAYER_SHORT:
        return LAYER_SHORT[s]
    for layer in LAYERS:
        if s in layer or layer in s:
            return layer
    sys.exit(f'没有这一层：{s}。可选 句子 / 段落 / 结构。')


def groups_of(words):
    """每个关键词连同它的别名算一组，组内任一命中即算这组命中。"""
    groups, expanded = [], []
    for w in words:
        key = w.lower()
        tgt = [t for t in ALIAS.get(key, []) if t not in words]
        groups.append([w] + tgt)
        if tgt:
            expanded.append(f"{w}→{'/'.join(tgt)}")
    return groups, expanded


def rank(groups, mode='and', strict=False, layer=None):
    """mode='and' 要求每组都命中；mode='or' 命中任意一组即可。"""
    scored = []
    for c in CARDS:
        if layer and c['layer'] != layer:
            continue
        head = (c['title'] + ' ' + c['effect']).lower()
        meta = (c['domain'] + ' ' + c['layer']).lower()
        body = c.get('body', '').lower()
        hay = head + ' ' + meta if strict else head + ' ' + meta + ' ' + body
        hit = [g for g in groups if any(w.lower() in hay for w in g)]
        if not hit or (mode == 'and' and len(hit) != len(groups)):
            continue
        score = 0.0
        for g in hit:
            has = [w.lower() for w in g if w.lower() in hay]
            score += max(3 if w in head else 1 for w in has)
        score += 0.5 if c['n'] > 1 else 0
        if mode == 'or':
            score /= len(groups)
        scored.append((score, len(hit), c))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]['gid']))
    return scored


def search(words, strict=False, layer=None, top=25):
    groups, expanded = groups_of(words)
    scored = rank(groups, 'and', strict, layer)
    note = ''
    if not scored and not strict:
        scored = rank(groups, 'or', strict, layer)
        note = '（没有全部命中的，以下是只命中部分关键词的）'
    scope = []
    if layer:
        scope.append(f'仅 {layer}')
    if strict:
        scope.append('strict：只比标题与效果')
    else:
        scope.append('已含正文匹配')
    if expanded:
        scope.append('别名展开 ' + '，'.join(expanded))
    print(f"检索 {len(words)} 个词｜{'｜'.join(scope)}")
    if not scored:
        print('\n没命中。换个更小的动作词，加 --layer 限定一层，或用 --domain 看某一主题域的全部卡片。')
        return
    print(f"\n命中 {len(scored)} 张{note}：\n")
    for s, h, c in scored[:top]:
        mark = ''
        if len(words) > 1:
            mark = '' if h == len(words) else f'（{h}/{len(words)}）'
        print(brief(c, '', mark))
    if len(scored) > top:
        print(f"\n…还有 {len(scored) - top} 张，加关键词收窄或用 --top 调。"
              f"要更干净的结果加 --strict。")


def domain(name):
    hit = [c for c in CARDS if name in c['domain']]
    if not hit:
        sys.exit('没有这个主题域。用 --list 看全部。')
    by = {}
    for c in hit:
        by.setdefault(c['layer'], []).append(c)
    print(f"主题域「{hit[0]['domain']}」共 {len(hit)} 张：\n")
    for layer in LAYERS:
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


# ── 引文核验 ──────────────────────────────────────────────

PUNCT = {'‘': "'", '’': "'", '“': '"', '”': '"',
         '–': '-', '—': '-', '−': '-', '‑': '-',
         ' ': ' ', ' ': ' ', ' ': ' '}


def norm(s):
    """归一化：统一引号破折号、折叠空白、忽略大小写。只为了比对，不改原义。"""
    s = unicodedata.normalize('NFC', s)
    for k, v in PUNCT.items():
        s = s.replace(k, v)
    s = s.replace('…', '...')
    return re.sub(r'\s+', ' ', s).strip().lower()


def blocks(path):
    """引文块：优先把连续的 `> ` 引用行当成一块；否则按空行分段。"""
    raw = open(path, encoding='utf-8').read()
    lines = raw.splitlines()
    if any(l.lstrip().startswith('>') for l in lines):
        out, cur = [], []
        for l in lines + ['']:
            t = l.lstrip()
            if t.startswith('>'):
                cur.append(t[1:].lstrip())
            elif cur:
                out.append(' '.join(cur).strip())
                cur = []
        return [b for b in out if b]
    return [b.strip() for b in re.split(r'\n\s*\n', raw) if b.strip()]


def longest_prefix(q, s):
    """q 里有多少字是能在 s 里接上的，用来定位断在哪。"""
    ws = q.split()
    ok = 0
    for k in range(len(ws), 0, -1):
        if ' '.join(ws[:k]) in s:
            ok = k
            break
    return ok, ws


def verify(src_path, quote_path):
    src = norm(open(src_path, encoding='utf-8').read())
    bs = blocks(quote_path)
    if not bs:
        sys.exit(f'{quote_path} 里没找到引文块')
    good = bad = warn = 0
    print(f"原文 {len(src)} 字（归一化后）｜引文块 {len(bs)} 条\n")
    for i, b in enumerate(bs, 1):
        q = norm(b)
        q = re.sub(r'^(\.\.\.)\s*', '', q)
        q = re.sub(r'\s*(\.\.\.)$', '', q)
        if not q:
            continue
        head = b.strip().replace('\n', ' ')[:58]
        if q in src:
            if '...' in q:
                warn += 1
                print(f"{i:>2} ⚠  含省略号，确认不是拼接  {head}")
            else:
                good += 1
                print(f"{i:>2} ✓  {head}")
            continue
        bad += 1
        k, ws = longest_prefix(q, src)
        if k < 3:                       # 一两个词的巧合命中不算接上
            k = 0
        tail = ' '.join(ws[k:k + 8]) if k < len(ws) else '（全句找不到）'
        print(f"{i:>2} ✗  {head}")
        print(f"     前 {k} 个词能接上，断在这里：{tail}")
        if '...' in q:
            print("     含省略号且接不上：很可能是把相隔较远的两句拼成了一句。")
        elif k == 0:
            print("     一个词都对不上：确认这段真是原文引文，不是转述或旁批。")
    print(f"\n逐字命中 {good}｜含省略号待确认 {warn}｜不合格 {bad}")
    if bad:
        sys.exit(1)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == '--gid':
        card_text(args[1])
        return
    if args[0] == '--domain':
        domain(args[1])
        return
    if args[0] == '--list':
        listing()
        return
    if args[0] == '--verify':
        if len(args) < 3:
            sys.exit('用法：--verify 原文.txt 引文.md')
        verify(args[1], args[2])
        return

    strict, layer, top, words = False, None, 25, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--strict':
            strict = True
            i += 1
        elif a in ('--layer', '--top'):
            if i + 1 >= len(args):
                sys.exit(f'{a} 后面要跟一个值')
            if a == '--layer':
                layer = norm_layer(args[i + 1])
            else:
                top = int(args[i + 1])
            i += 2
        elif a.startswith('--'):
            sys.exit(f'不认识的参数：{a}')
        else:
            words.extend(a.split())
            i += 1
    if not words:
        sys.exit('给个关键词，或用 --gid / --domain / --list / --verify')
    search(words, strict, layer, top)


main()
