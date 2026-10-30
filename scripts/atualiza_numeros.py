# -*- coding: utf-8 -*-
"""Regenera heatmap-*.svg e numeros-*.svg com dados frescos da API do GitHub.

Roda sozinho pelo workflow .github/workflows/atualiza-numeros.yml.
Sem dependencia externa: so biblioteca padrao.

Token: usa GH_PAT quando existir e cai para GITHUB_TOKEN caso contrario. Para o
numero de projetos contar os privados, o GH_PAT precisa enxergar todos os
repositorios (fine-grained: "All repositories" com Metadata read-only).
"""
import os, io, json, math, datetime, urllib.request
from xml.sax.saxutils import escape

USUARIO = os.environ.get('GH_USER', 'cesarkali')
TOKEN   = os.environ.get('GH_PAT') or os.environ.get('GITHUB_TOKEN')
RAIZ    = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ASSETS  = os.path.join(RAIZ, 'assets')

SANS = u"'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
MONO = u"'Cascadia Mono','JetBrains Mono',Consolas,'SF Mono','Roboto Mono',monospace"

# paleta do caliberda.com.br: tinta + azul ultramar ("teal" e "coral" mantêm o
# nome antigo só para não mexer no resto do script)
TEMAS = {
 'dark':  dict(ink='#E8E9EC', dim='#9A9CA3', faint='#2A2C33', teal='#7D8DFF', coral='#B8C1FF',
               cel=['#161B22', '#1F2A6B', '#3143B8', '#5468F0', '#8E9CFF'],
               cobra=['#F2F3F5', '#DCDEE3', '#BFC2CA', '#9A9EA8', '#747884']),
 'light': dict(ink='#0E0E0F', dim='#5B5B60', faint='#DCDCD6', teal='#1A36E6', coral='#0E0E0F',
               cel=['#EEEEEA', '#C9D0FB', '#8E9CF4', '#4A61EE', '#1A36E6'],
               cobra=['#3A3A3F', '#2C2C31', '#1F1F23', '#141417', '#0A0A0B']),
}

MES = {
 'pt': [u'jan', u'fev', u'mar', u'abr', u'mai', u'jun', u'jul', u'ago', u'set', u'out', u'nov', u'dez'],
 'en': [u'jan', u'feb', u'mar', u'apr', u'may', u'jun', u'jul', u'aug', u'sep', u'oct', u'nov', u'dec'],
}

FRASE = {
 'pt': u'<tspan font-weight="700" fill="%(teal)s">%(T)d</tspan> contribuições espalhadas por '
       u'<tspan font-weight="700" fill="%(teal)s">%(A)d</tspan> dias. O maior deles teve '
       u'<tspan font-weight="700" fill="%(coral)s">%(P)d</tspan>.',
 'en': u'<tspan font-weight="700" fill="%(teal)s">%(T)d</tspan> contributions spread across '
       u'<tspan font-weight="700" fill="%(teal)s">%(A)d</tspan> days. The busiest one had '
       u'<tspan font-weight="700" fill="%(coral)s">%(P)d</tspan>.',
}

ROTULOS = {
 'pt': [(u'projetos', u'em %d meses'), (u'contribuições', u'no último ano'),
        (u'dias', u'com entrega nova'), (u'delas', u'em repositório privado')],
 'en': [(u'projects', u'in %d months'), (u'contributions', u'in the last year'),
        (u'days', u'with something new'), (u'of them', u'in private repos')],
}


def destino(idioma, nome):
    d = ASSETS if idioma == 'pt' else os.path.join(ASSETS, 'en')
    if not os.path.isdir(d):
        os.makedirs(d)
    return os.path.join(d, nome)


def consulta():
    hoje = datetime.datetime.now(datetime.timezone.utc)
    desde = hoje - datetime.timedelta(days=365)
    q = '''
    query($login:String!, $de:DateTime!, $ate:DateTime!) {
      user(login:$login) {
        repositories(first:100, ownerAffiliations:OWNER, isFork:false) {
          totalCount
          nodes { createdAt }
        }
        publicos: repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC) { totalCount }
        contributionsCollection(from:$de, to:$ate) {
          commitContributionsByRepository(maxRepositories:100) {
            repository { isPrivate } contributions { totalCount } }
          issueContributionsByRepository(maxRepositories:100) {
            repository { isPrivate } contributions { totalCount } }
          pullRequestContributionsByRepository(maxRepositories:100) {
            repository { isPrivate } contributions { totalCount } }
          pullRequestReviewContributionsByRepository(maxRepositories:100) {
            repository { isPrivate } contributions { totalCount } }
          repositoryContributions(first:100) { nodes { repository { isPrivate } } }
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }'''
    corpo = json.dumps({'query': q, 'variables': {
        'login': USUARIO,
        'de': desde.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'ate': hoje.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }}).encode('utf-8')

    req = urllib.request.Request('https://api.github.com/graphql', data=corpo)
    req.add_header('Authorization', 'Bearer %s' % TOKEN)
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'perfil-%s' % USUARIO)
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode('utf-8'))
    if 'errors' in d:
        raise SystemExit('GraphQL falhou: %s' % d['errors'])
    return d['data']['user']


def publicas(cc):
    """Contribuicoes feitas em repositorio publico, somadas repo a repo.

    O resto do total do calendario e privado. Nao da para usar
    restrictedContributionsCount: ele so conta o que o token NAO enxerga, entao
    cai para zero justamente quando o token tem acesso aos privados."""
    n = 0
    for chave in ('commitContributionsByRepository', 'issueContributionsByRepository',
                  'pullRequestContributionsByRepository', 'pullRequestReviewContributionsByRepository'):
        n += sum(r['contributions']['totalCount'] for r in cc[chave]
                 if not r['repository']['isPrivate'])
    n += sum(1 for r in cc['repositoryContributions']['nodes'] if not r['repository']['isPrivate'])
    return n


def nivel(n):
    if n == 0: return 0
    if n <= 2: return 1
    if n <= 5: return 2
    if n <= 12: return 3
    return 4


def heatmap(t, semanas, total, ativos, pico, idioma='pt'):
    """Grade de contribuicoes com uma cobra que percorre o ano comendo os dias.

    A cobra anda em zigue-zague, coluna por coluna. Cada celula com contribuicao
    apaga no instante exato em que a cabeca passa por cima, e todas reacendem no
    fim da volta. Sem SMIL, a grade continua correta e so nao ha cobra."""
    CEL, GAP = 11.0, 3.4
    P = CEL + GAP
    X0, Y0 = 44.0, 46.0
    NW = len(semanas)
    W = X0 + NW * P + 20
    H = Y0 + 7 * P + 56
    DUR = 26.0                      # uma volta inteira

    # ordem de visita: desce uma coluna, sobe a seguinte
    caminho = []
    for iw in range(NW):
        linhas = range(7) if iw % 2 == 0 else range(6, -1, -1)
        for row in linhas:
            caminho.append((iw, row))
    passos = len(caminho)
    VOLTA = 0.90          # fracao do ciclo em que a cobra percorre a grade
    quando = {pos: (i / float(passos)) * VOLTA for i, pos in enumerate(caminho)}

    comiveis = set()      # posicoes do trajeto que valem uma refeicao
    cels, rots, visto = [], [], set()
    for iw, w in enumerate(semanas):
        for dd in w['contributionDays']:
            dt = datetime.date(*map(int, dd['date'].split('-')))
            row = (dt.weekday() + 1) % 7
            x, y = X0 + iw * P, Y0 + row * P
            lv = nivel(dd['contributionCount'])
            anim = u''
            if lv > 0:
                comiveis.add((iw, row))
                k = quando.get((iw, row), 0.0)
                k1 = min(k + 0.004, VOLTA + 0.02)
                # acesa -> a cabeca chega -> apagada -> reacende no fim da volta
                anim = (u'<animate attributeName="fill" values="%s;%s;%s;%s;%s" '
                        u'keyTimes="0;%.4f;%.4f;0.965;1" dur="%ss" repeatCount="indefinite"/>'
                        % (t['cel'][lv], t['cel'][lv], t['cel'][0], t['cel'][0], t['cel'][lv],
                           k, k1, DUR))
            cels.append(u'<rect x="%.1f" y="%.1f" width="%.0f" height="%.0f" fill="%s">%s</rect>'
                        % (x, y, CEL, CEL, t['cel'][lv], anim))
            if dt.day <= 7 and dt.month not in visto:
                visto.add(dt.month)
                rots.append(u'<text x="%.1f" y="%.1f" class="s" fill="%s">%s</text>'
                            % (x, Y0 - 11, t['dim'], MES[idioma][dt.month - 1]))

    # o trajeto, pelo centro de cada celula
    meio = CEL / 2.0
    pts = [(X0 + iw * P + meio, Y0 + row * P + meio) for iw, row in caminho]
    trilho = u'M' + u' L'.join(u'%.1f %.1f' % pt for pt in pts)

    # a cobra cresce: comeca com tres blocos e ganha um a cada punhado de dias comidos
    N_SEG, INICIAIS = 15, 3
    passo_t = VOLTA / float(passos)

    # instante em que cada refeicao acontece, na ordem do trajeto
    refeicoes = [quando[pos] for pos in caminho if pos in comiveis]
    novos = max(1, N_SEG - INICIAIS)

    corpo = []
    for k in range(N_SEG):
        atraso = k * passo_t
        lado = 11.0 - (k * 4.6 / float(N_SEG))          # afina da cabeca para a cauda
        cor = t['cobra'][min(k * len(t['cobra']) // N_SEG, len(t['cobra']) - 1)]
        inicio = -(DUR - atraso * DUR) if atraso else 0.0

        if k < INICIAIS or not refeicoes:
            surge, op = u'', u'1'
        else:
            # nasce depois de comer a fracao correspondente dos dias do ano
            i = min(int(((k - INICIAIS + 1) / float(novos)) * len(refeicoes)), len(refeicoes) - 1)
            nasce = min(refeicoes[i] + atraso, VOLTA)
            surge = (u'<animate attributeName="opacity" values="0;0;1;1;0" '
                     u'keyTimes="0;%.4f;%.4f;0.95;1" dur="%ss" repeatCount="indefinite"/>'
                     % (nasce, min(nasce + 0.004, 0.94), DUR))
            op = u'0'

        corpo.append(
            u'<rect x="%.2f" y="%.2f" width="%.1f" height="%.1f" fill="%s" opacity="%s">'
            u'<animateMotion dur="%ss" repeatCount="indefinite" begin="%.3fs" calcMode="linear" '
            u'keyPoints="0;1;1" keyTimes="0;0.90;1">'
            u'<mpath xlink:href="#trilho" href="#trilho"/></animateMotion>%s</rect>'
            % (-lado/2.0, -lado/2.0, lado, lado, cor, op, DUR, inicio, surge))

    return u'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 %(W).0f %(H).0f" width="%(W).0f" height="%(H).0f" role="img" aria-label="Mapa de contribuições do último ano: %(T)d contribuições em %(A)d dias, com uma cobra percorrendo a grade.">
  <title>O ano inteiro, dia a dia</title>
  <defs><path id="trilho" d="%(TRILHO)s" fill="none"/></defs>
  <style>
    .s { font-family: %(MONO)s; font-size: 10.5px; letter-spacing: 1px; }
    .b { font-family: %(SANS)s; font-size: 14px; }
  </style>
  %(ROTS)s
  %(CELS)s
  %(COBRA)s
  <text x="%(X0).1f" y="%(TY).1f" class="b" fill="%(dim)s">%(FRASE)s</text>
</svg>
''' % dict(W=W, H=H, MONO=MONO, SANS=SANS, ROTS=u'\n  '.join(rots), CELS=u'\n  '.join(cels),
           COBRA=u'\n  '.join(corpo), TRILHO=trilho, X0=X0, TY=Y0 + 7 * P + 30, T=total, A=ativos, P=pico,
           FRASE=FRASE[idioma] % dict(T=total, A=ativos, P=pico, teal=t['teal'], coral=t['coral']),
           dim=t['dim'], teal=t['teal'], coral=t['coral'])


def numeros(t, itens):
    W, H = 1000, 190
    DH = 76.0
    X0, PASSO = 54.0, 242.0
    BASE = 96.0

    grupos, cortes = [], []
    for i, (val, rot, sub) in enumerate(itens):
        x = X0 + i * PASSO
        digitos = []
        for j, ch in enumerate(val):
            dx = x + j * 42
            alvo = int(ch)
            yfin = -alvo * DH
            yini = -(alvo + 10 * (2 + (j + i) % 2)) * DH
            col = u''.join(u'<text x="0" y="%.1f" class="n">%d</text>' % (k * DH, k % 10)
                           for k in range(alvo + 31))
            digitos.append(
                u'<g clip-path="url(#c%d_%d)"><g transform="translate(%.1f,%.1f)">'
                u'<animateTransform attributeName="transform" type="translate" '
                u'values="%.1f,%.1f;%.1f,%.1f" keyTimes="0;1" dur="1.9s" begin="%.2fs" '
                u'calcMode="spline" keySplines="0.16 0.84 0.24 1" fill="freeze"/>%s</g></g>'
                % (i, j, dx, BASE + yfin, dx, BASE + yini, dx, BASE + yfin, 0.12 * (i * 3 + j), col))
            cortes.append(u'<clipPath id="c%d_%d"><rect x="%.1f" y="%.1f" width="40" height="66"/></clipPath>'
                          % (i, j, dx - 3, BASE - 58))
        grupos.append(u'<g>%s</g>' % u''.join(digitos))
        grupos.append(u'<text x="%.1f" y="%.1f" class="l" fill="%s">%s</text>'
                      u'<text x="%.1f" y="%.1f" class="s" fill="%s">%s</text>'
                      % (x, BASE + 30, t['teal'], rot, x, BASE + 50, t['dim'], sub))

    alt = u', '.join(u'%s %s %s' % (v, r, s) for v, r, s in itens)
    return u'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %(W)d %(H)d" width="%(W)d" height="%(H)d" role="img" aria-label="%(ALT)s.">
  <title>Os números, sem maquiagem</title>
  <defs>%(CORTES)s</defs>
  <style>
    .n { font-family: %(SANS)s; font-size: 62px; font-weight: 700; fill: %(ink)s; }
    .l { font-family: %(SANS)s; font-size: 15px; font-weight: 600; }
    .s { font-family: %(MONO)s; font-size: 11.5px; letter-spacing: 1.2px; }
  </style>
  %(GRUPOS)s
</svg>
''' % dict(W=W, H=H, SANS=SANS, MONO=MONO, ink=t['ink'], ALT=alt,
           CORTES=u''.join(cortes), GRUPOS=u'\n  '.join(grupos))


# ─────────────────────────── WINDHAWK ─────────────────────────
# O catálogo público que o próprio programa do Windhawk consulta. "users" é quem
# está com o mod instalado; a nota vai de 0 a 10 e ratingBreakdown conta as
# avaliações de 1 a 5 estrelas.
CATALOGO_WH = 'https://mods.windhawk.net/catalog.json'
MODS_WH = ['alt-tab-flip-3d', 'mac-island-dock']

COR_WH = dict(bg='#080C14', ink='#EAF2FF', dim='#AFC0D6', mut='#6E8099', acc='#5AB4FF', star='#FFC857',
              linha='#FFFFFF', fatias=['#5AB4FF', '#A9D6FF', '#3D5878'])

# os mods somados no card de números; as faixas de usuários saem só para MODS_WH
MODS_TODOS = MODS_WH + ['windows-terminal-start-minimized']
REPO_WH = 'ramensoftware/windhawk-mods'
FONTE_WH = 'https://raw.githubusercontent.com/%s/main/mods/%%s.wh.cpp' % REPO_WH

MES_CURTO = {
 'pt': [u'JAN', u'FEV', u'MAR', u'ABR', u'MAI', u'JUN', u'JUL', u'AGO', u'SET', u'OUT', u'NOV', u'DEZ'],
 'en': [u'JAN', u'FEB', u'MAR', u'APR', u'MAY', u'JUN', u'JUL', u'AUG', u'SEP', u'OCT', u'NOV', u'DEC'],
}

TXT_WH = {
 'pt': dict(users=u'PESSOAS USANDO', aval=(u'AVALIAÇÃO', u'AVALIAÇÕES'), sem=u'AINDA SEM AVALIAÇÃO',
            fonte=u'DADOS DE %s', dec=u','),
 'en': dict(users=u'PEOPLE USING IT', aval=(u'RATING', u'RATINGS'), sem=u'NO RATINGS YET',
            fonte=u'AS OF %s', dec=u'.'),
}


def catalogo_wh():
    req = urllib.request.Request(CATALOGO_WH)
    req.add_header('User-Agent', 'perfil-%s' % USUARIO)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8'))['mods']


def milhar(n, idioma):
    return u'{:,}'.format(n).replace(u',', u'.' if idioma == 'pt' else u',')


def hoje_curto(idioma, ano=True):
    h = datetime.date.today()
    s = u'%d %s' % (h.day, MES_CURTO[idioma][h.month - 1])
    return u'%s %d' % (s, h.year) if ano else s


def media_votos(votos):
    n = sum(votos)
    return (sum((i + 1) * v for i, v in enumerate(votos)) / float(n) if n else 0.0), n


def estrela(x, y, r, cor, extra=u''):
    """Estrela de cinco pontas com centro em (x, y) e raio externo r."""
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append(u'%.2f %.2f' % (x + rr * math.cos(a), y - rr * math.sin(a)))
    return u'<path d="M%s Z" fill="%s"%s/>' % (u' L'.join(pts), cor, extra)


def faixa_wh(mod, idioma):
    """Faixa logo abaixo do card do mod: quem usa, a nota com as estrelas, como
    as avaliações se distribuem de 5 a 1 estrela, e a versão."""
    c, L = COR_WH, TXT_WH[idioma]
    det, meta = mod['details'], mod['metadata']
    votos = det.get('ratingBreakdown') or [0] * 5
    media, n = media_votos(votos)
    users = milhar(det.get('users', 0), idioma)
    nota = (u'%.1f' % media).replace(u'.', L['dec']) if n else u'–'

    # estrelas logo depois da nota, preenchidas pela média
    x0 = 296 + len(nota) * 19.5 + 14
    est = []
    for i in range(5):
        cx = x0 + i * 19
        cheio = max(0.0, min(1.0, media - i))
        est.append(u'<clipPath id="f%d"><rect x="%.1f" y="22" width="%.1f" height="20"/></clipPath>%s%s'
                   % (i, cx - 8, 16 * cheio, estrela(cx, 33, 8, c['mut'], u' opacity=".35"'),
                      estrela(cx, 33, 8, c['star'], u' clip-path="url(#f%d)"' % i)))

    # distribuição: uma barra por quantidade de estrelas, a maior ocupa a trilha inteira
    maior = float(max(votos) or 1)
    barras = []
    for k, i in enumerate(range(4, -1, -1)):
        y = 19 + k * 11
        w = 190 * votos[i] / maior
        barras.append(u'<text x="606" y="%.1f" class="d">%d</text>'
                      u'<rect x="620" y="%.1f" width="190" height="4" rx="2" fill="%s" opacity=".08"/>'
                      u'<rect x="620" y="%.1f" width="%.1f" height="4" rx="2" fill="%s">'
                      u'<animate attributeName="width" values="0;%.1f" dur="1.1s" begin="%.2fs" calcMode="spline" keySplines="0.2 0.7 0.3 1" fill="freeze"/></rect>'
                      % (y + 4.5, i + 1, y, c['linha'], y, w, c['acc'] if i == 4 else c['dim'], w, 0.08 * k))

    versao = meta.get('version', u'?')
    return u'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 88" width="1000" height="88" role="img" aria-label="%(alt)s">
  <title>%(nome)s no Windhawk</title>
  <style>
    .n { font-family: %(SANS)s; font-size: 34px; font-weight: 800; fill: %(ink)s; letter-spacing: -.8px; font-variant-numeric: tabular-nums; }
    .l { font-family: %(MONO)s; font-size: 10px; letter-spacing: 1.6px; fill: %(mut)s; }
    .d { font-family: %(MONO)s; font-size: 9px; fill: %(mut)s; text-anchor: end; }
    .v { font-family: %(MONO)s; font-size: 11.5px; letter-spacing: 1px; fill: %(acc)s; text-anchor: middle; }
  </style>
  <rect x=".5" y=".5" width="999" height="87" rx="12" fill="%(bg)s" stroke="%(acc)s" stroke-opacity=".28"/>
  <path d="M13 .5 H987" stroke="%(linha)s" stroke-opacity=".07"/>
  <text x="30" y="48" class="n">%(users)s</text>
  <text x="30" y="70" class="l">%(lu)s</text>
  <path d="M262 18 V70" stroke="%(linha)s" stroke-opacity=".08"/>
  <text x="296" y="48" class="n">%(nota)s</text>
  %(EST)s
  <text x="296" y="70" class="l">%(lav)s</text>
  <path d="M574 18 V70" stroke="%(linha)s" stroke-opacity=".08"/>
  %(BARRAS)s
  <path d="M846 18 V70" stroke="%(linha)s" stroke-opacity=".08"/>
  <rect x="872" y="24" width="100" height="24" rx="12" fill="%(acc)s" fill-opacity=".08" stroke="%(acc)s" stroke-opacity=".45"/>
  <text x="922" y="40" class="v">v%(versao)s</text>
  <text x="922" y="70" class="l" text-anchor="middle">%(fonte)s</text>
</svg>
''' % dict(SANS=SANS, MONO=MONO, nome=escape(meta.get('name', '')), users=users, lu=L['users'],
           nota=nota, EST=u''.join(est), BARRAS=u'\n  '.join(barras), versao=escape(versao),
           lav=(u'%s %s' % (milhar(n, idioma), L['aval'][n != 1])) if n else L['sem'],
           fonte=L['fonte'] % hoje_curto(idioma, ano=False),
           alt=u'%s %s, %s' % (users, L['users'].lower(), nota), **c)


# ───────────────────────── OS MODS EM NÚMEROS ─────────────────────────
# Um card só para os mods publicados: quem usa (com a fatia de cada mod), a
# nota média, o tamanho do código lido do repositório oficial e o ritmo.
TXT_NUM = {
 'pt': dict(h=u'OS MODS DO WINDHAWK EM NÚMEROS', atual=u'ATUALIZADO EM %s',
            hero=u'pessoas usando os %d mods',
            itens=[(u'de 5 estrelas', u'média de %(avaliacoes)s avaliações'),
                   (u'linhas de C++', u'em %(n_mods)d arquivos abertos'),
                   (u'versões publicadas', u'%(prs)d PRs aceitos no Windhawk'),
                   (u'idiomas', u'na interface da ilha'),
                   (u'dias no ar', u'desde o primeiro mod'),
                   (u'mods publicados', u'no catálogo oficial')],
            fim=u'Tudo em código aberto no repositório oficial do Windhawk. Cada versão passa pela revisão de um mantenedor antes de chegar a você.'),
 'en': dict(h=u'THE WINDHAWK MODS IN NUMBERS', atual=u'UPDATED %s',
            hero=u'people using the %d mods',
            itens=[(u'out of 5 stars', u'average of %(avaliacoes)s ratings'),
                   (u'lines of C++', u'in %(n_mods)d open source files'),
                   (u'versions released', u'%(prs)d PRs merged into Windhawk'),
                   (u'languages', u'in the island&apos;s interface'),
                   (u'days live', u'since the first mod'),
                   (u'mods published', u'in the official catalog')],
            fim=u'All open source in the official Windhawk repository. Every release is reviewed by a maintainer before it reaches you.'),
}


def api_github(caminho):
    req = urllib.request.Request('https://api.github.com/' + caminho)
    req.add_header('Authorization', 'Bearer %s' % TOKEN)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('User-Agent', 'perfil-%s' % USUARIO)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8'))


def linhas_de_codigo(mid):
    """Linhas não vazias do .cpp, sem o README e as configurações, que moram em
    comentários dentro do próprio arquivo. Devolve também quantos idiomas a
    interface do mod tem (kTextLanguages), ou 1 se ele não traduz nada."""
    req = urllib.request.Request(FONTE_WH % mid)
    req.add_header('User-Agent', 'perfil-%s' % USUARIO)
    with urllib.request.urlopen(req, timeout=45) as r:
        linhas = r.read().decode('utf-8').split('\n')
    codigo, dentro, idiomas = 0, False, 1
    for l in linhas:
        if '==WindhawkModReadme==' in l or '==WindhawkModSettings==' in l:
            dentro = True
        if not dentro and l.strip():
            codigo += 1
        if '==/WindhawkModReadme==' in l or '==/WindhawkModSettings==' in l:
            dentro = False
        if l.startswith('constexpr int kTextLanguages ='):
            idiomas = int(l.split('=')[1].strip(' ;'))
    return codigo, idiomas


def versoes_publicadas(mid):
    """Cada versão publicada é um PR aceito que mexeu no arquivo do mod."""
    total, pagina = 0, 1
    while True:
        lote = api_github('repos/%s/commits?path=mods/%s.wh.cpp&per_page=100&page=%d' % (REPO_WH, mid, pagina))
        total += len(lote)
        if len(lote) < 100:
            return total
        pagina += 1


def dados_mods(mods):
    """Os números do card, somados entre os mods publicados. Cada um vem de uma
    fonte só (catálogo do Windhawk ou o repositório oficial), sem estimativa."""
    publicados = [m for m in MODS_TODOS if m in mods]
    votos, codigo, idiomas, versoes, por_mod = [0] * 5, 0, 1, 0, []
    for mid in publicados:
        det = mods[mid]['details']
        votos = [a + b for a, b in zip(votos, det.get('ratingBreakdown') or [0] * 5)]
        linhas, idi = linhas_de_codigo(mid)
        codigo += linhas
        idiomas = max(idiomas, idi)
        versoes += versoes_publicadas(mid)
        por_mod.append(dict(id=mid, nome=mods[mid]['metadata'].get('name', mid), usuarios=det.get('users', 0)))
    media, n = media_votos(votos)
    primeiro = min(mods[m]['details']['published'] for m in publicados) / 1000.0
    dias = (datetime.date.today() - datetime.datetime.fromtimestamp(primeiro, datetime.timezone.utc).date()).days
    prs = api_github('search/issues?q=repo:%s+is:pr+is:merged+author:%s' % (REPO_WH, USUARIO))['total_count']
    return dict(usuarios=sum(m['usuarios'] for m in por_mod), media=media, avaliacoes=n, codigo=codigo,
                versoes=versoes, prs=prs, idiomas=idiomas, dias=dias, n_mods=len(publicados),
                por_mod=sorted(por_mod, key=lambda m: -m['usuarios']))


def card_mods(d, idioma):
    """O total de quem usa em destaque, a fatia de cada mod numa barra, e seis
    números ao lado separados por linhas finas."""
    c, L = COR_WH, TXT_NUM[idioma]
    fmt = dict(avaliacoes=milhar(d['avaliacoes'], idioma), n_mods=d['n_mods'], prs=d['prs'])
    vals = [(u'%.1f' % d['media']).replace(u'.', TXT_WH[idioma]['dec']), milhar(d['codigo'], idioma),
            str(d['versoes']), str(d['idiomas']), str(d['dias']), str(d['n_mods'])]

    # barra com a fatia de cada mod, e a legenda logo abaixo
    total = float(d['usuarios'] or 1)
    x, fatias, legenda = 36.0, [], []
    for k, m in enumerate(d['por_mod']):
        w = max(2.0, 320 * m['usuarios'] / total - (2 if k < len(d['por_mod']) - 1 else 0))
        cor = c['fatias'][min(k, len(c['fatias']) - 1)]
        fatias.append(u'<rect x="%.1f" y="186" width="%.1f" height="8" rx="4" fill="%s">'
                      u'<animate attributeName="width" values="0;%.1f" dur="1.2s" begin="%.2fs" calcMode="spline" keySplines="0.2 0.7 0.3 1" fill="freeze"/></rect>'
                      % (x, w, cor, w, 0.15 * k))
        x += w + 2
        y = 222 + k * 22
        legenda.append(u'<circle cx="40" cy="%.1f" r="4" fill="%s"/><text x="52" y="%.1f" class="g">%s</text>'
                       u'<text x="356" y="%.1f" class="q">%s · %d%%</text>'
                       % (y - 4, cor, y, escape(m['nome']), y, milhar(m['usuarios'], idioma),
                          round(100 * m['usuarios'] / total)))

    grade = []
    for i, (val, (rot, sub)) in enumerate(zip(vals, L['itens'])):
        gx, gy = 444 + (i % 3) * 176, 118 + (i // 3) * 104
        extra = estrela(gx + len(val) * 21 + 16, gy - 14, 9, c['star']) if i == 0 else u''
        grade.append(u'<text x="%d" y="%d" class="m">%s</text>%s<text x="%d" y="%d" class="r">%s</text>'
                     u'<text x="%d" y="%d" class="s">%s</text>' % (gx, gy, val, extra, gx, gy + 24, rot, gx, gy + 42, sub % fmt))

    alt = u'%s %s; ' % (milhar(d['usuarios'], idioma), L['hero'] % d['n_mods']) + u', '.join(
        u'%s %s' % (v, r) for v, (r, s) in zip(vals, L['itens']))
    return u'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 330" width="1000" height="330" role="img" aria-label="%(ALT)s.">
  <title>%(H)s</title>
  <style>
    .h { font-family: %(MONO)s; font-size: 11px; letter-spacing: 2.4px; }
    .big { font-family: %(SANS)s; font-size: 66px; font-weight: 800; fill: %(ink)s; letter-spacing: -2px; font-variant-numeric: tabular-nums; }
    .hl { font-family: %(SANS)s; font-size: 15px; fill: %(dim)s; }
    .g { font-family: %(SANS)s; font-size: 13px; fill: %(dim)s; }
    .q { font-family: %(MONO)s; font-size: 11px; fill: %(mut)s; text-anchor: end; }
    .m { font-family: %(SANS)s; font-size: 36px; font-weight: 800; fill: %(ink)s; letter-spacing: -1px; font-variant-numeric: tabular-nums; }
    .r { font-family: %(SANS)s; font-size: 14px; font-weight: 600; fill: %(ink)s; }
    .s { font-family: %(SANS)s; font-size: 12.5px; fill: %(dim)s; }
    .f { font-family: %(SANS)s; font-size: 12.5px; fill: %(mut)s; }
  </style>
  <rect x=".5" y=".5" width="999" height="329" rx="14" fill="%(bg)s" stroke="%(acc)s" stroke-opacity=".28"/>
  <path d="M15 .5 H985" stroke="%(linha)s" stroke-opacity=".07"/>
  <text x="36" y="40" class="h" fill="%(acc)s">%(H)s</text>
  <text x="964" y="40" class="h" fill="%(mut)s" text-anchor="end">%(ATUAL)s</text>
  <path d="M36 58 H964" stroke="%(linha)s" stroke-opacity=".08"/>
  <text x="32" y="140" class="big">%(USERS)s</text>
  <text x="36" y="168" class="hl">%(HERO)s</text>
  %(FATIAS)s
  %(LEGENDA)s
  <path d="M412 80 V284" stroke="%(linha)s" stroke-opacity=".08"/>
  <path d="M444 172 H964" stroke="%(linha)s" stroke-opacity=".08"/>
  <path d="M608 80 V284 M784 80 V284" stroke="%(linha)s" stroke-opacity=".05"/>
  %(GRADE)s
  <path d="M36 296 H964" stroke="%(linha)s" stroke-opacity=".08"/>
  <text x="36" y="318" class="f">%(FIM)s</text>
</svg>
''' % dict(ALT=alt, H=L['h'], ATUAL=L['atual'] % hoje_curto(idioma), USERS=milhar(d['usuarios'], idioma),
           HERO=L['hero'] % d['n_mods'], FATIAS=u''.join(fatias), LEGENDA=u'\n  '.join(legenda),
           GRADE=u'\n  '.join(grade), FIM=L['fim'], MONO=MONO, SANS=SANS, **c)


def atualiza_windhawk():
    """Regrava as faixas e o card de números; devolve ({mod: usuários}, números
    dos mods), que decidem a ordem dos mods e o texto do README."""
    # se o catálogo falhar, os números do GitHub seguem sendo publicados
    try:
        mods = catalogo_wh()
    except Exception as e:
        print('::warning::catálogo do Windhawk indisponível: %s' % e)
        return None, None
    usuarios = {}
    for mid in MODS_WH:
        if mid not in mods:
            print('::warning::%s ainda não está no catálogo do Windhawk' % mid)
            continue
        for idioma in ('pt', 'en'):
            io.open(destino(idioma, 'wh-%s.svg' % mid), 'w', encoding='utf-8', newline='\n').write(
                faixa_wh(mods[mid], idioma))
        det = mods[mid]['details']
        usuarios[mid] = det.get('users', 0)
        print('windhawk %s: %d usuarios | nota %s | %d avaliacoes'
              % (mid, det.get('users', 0), det.get('rating'), det.get('ratingUsers', 0)))
    try:
        d = dados_mods(mods)
        for idioma in ('pt', 'en'):
            io.open(destino(idioma, 'mods-windhawk.svg'), 'w', encoding='utf-8', newline='\n').write(card_mods(d, idioma))
        print('mods: %(usuarios)d usuarios | %(codigo)d linhas | %(versoes)d versoes | %(prs)d PRs | '
              '%(idiomas)d idiomas | %(dias)d dias' % d)
    except Exception as e:
        # um arquivo ou a API fora do ar: o card de ontem continua valendo
        print('::warning::card dos mods não atualizado hoje: %s' % e)
        d = None
    return usuarios, d


def grava_numeros(valores, meses, windhawk):
    """scripts/numeros.json alimenta o texto do README (gera_readme.py). O que
    falhar hoje (catálogo do Windhawk, código dos mods) fica com o valor de ontem."""
    caminho = os.path.join(RAIZ, 'scripts', 'numeros.json')
    try:
        ontem = json.load(io.open(caminho, encoding='utf-8'))
    except (IOError, ValueError):
        ontem = {}
    usuarios, mods = windhawk
    n = dict(repos=int(valores[0]), meses=meses, contrib=int(valores[1]), dias=int(valores[2]),
             privadas=int(valores[3]),
             windhawk=usuarios if usuarios is not None else ontem.get('windhawk', {}),
             mods=mods if mods is not None else ontem.get('mods', {}))
    io.open(caminho, 'w', encoding='utf-8', newline='\n').write(json.dumps(n, indent=2) + u'\n')


def main():
    if not TOKEN:
        raise SystemExit('faltou GH_PAT ou GITHUB_TOKEN no ambiente')

    u = consulta()
    cal = u['contributionsCollection']['contributionCalendar']
    semanas = cal['weeks']
    dias = [d for w in semanas for d in w['contributionDays']]
    total = cal['totalContributions']
    ativos = sum(1 for d in dias if d['contributionCount'] > 0)
    pico = max(d['contributionCount'] for d in dias)
    privadas = max(0, total - publicas(u['contributionsCollection']))

    repos = u['repositories']
    n_repos = repos['totalCount']
    if n_repos == u['publicos']['totalCount']:
        # o token so enxerga repositorio publico: o numero de projetos sai baixo
        print('::warning::o token so enxerga repositorios publicos (%d). Para contar os privados, '
              'de ao GH_PAT acesso a "All repositories" (Metadata: read-only basta).' % n_repos)
    datas = sorted(r['createdAt'][:10] for r in repos['nodes'])
    if datas:
        d0 = datetime.date(*map(int, datas[0].split('-')))
        hoje = datetime.date.today()
        meses = max(1, (hoje.year - d0.year) * 12 + (hoje.month - d0.month))
    else:
        meses = 1

    valores = [str(n_repos), str(total), str(ativos), str(privadas)]

    for idioma in ('pt', 'en'):
        rots = ROTULOS[idioma]
        itens = [(valores[i],
                  rots[i][0],
                  (rots[i][1] % meses) if '%d' in rots[i][1] else rots[i][1])
                 for i in range(4)]
        for nome, t in TEMAS.items():
            io.open(destino(idioma, 'heatmap-%s.svg' % nome), 'w', encoding='utf-8').write(
                heatmap(t, semanas, total, ativos, pico, idioma))
            io.open(destino(idioma, 'numeros-%s.svg' % nome), 'w', encoding='utf-8').write(
                numeros(t, itens))

    print('ok: %d repositorios | %d contribuicoes | %d dias | %d privadas | %d meses'
          % (n_repos, total, ativos, privadas, meses))

    grava_numeros(valores, meses, atualiza_windhawk())


if __name__ == '__main__':
    main()
