# -*- coding: utf-8 -*-
"""Regenera heatmap-*.svg e numeros-*.svg com dados frescos da API do GitHub.

Roda sozinho pelo workflow .github/workflows/atualiza-numeros.yml.
Sem dependencia externa: so biblioteca padrao.

Token: usa GH_PAT quando existir e cai para GITHUB_TOKEN caso contrario. Para o
numero de projetos contar os privados, o GH_PAT precisa enxergar todos os
repositorios (fine-grained: "All repositories" com Metadata read-only).
"""
import os, io, json, datetime, urllib.request
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

COR_WH = dict(bg='#06090F', ink='#EAF2FF', dim='#AFC0D6', mut='#6E8099', acc='#5AB4FF', star='#FFC857')

TXT_WH = {
 'pt': dict(users=u'pessoas usando', aval=(u'avaliação', u'avaliações'), sem=u'ainda sem avaliação',
            versao=u'VERSÃO %s · DADOS DO WINDHAWK', dec=u','),
 'en': dict(users=u'people using it', aval=(u'rating', u'ratings'), sem=u'no ratings yet',
            versao=u'VERSION %s · WINDHAWK DATA', dec=u'.'),
}


def catalogo_wh():
    req = urllib.request.Request(CATALOGO_WH)
    req.add_header('User-Agent', 'perfil-%s' % USUARIO)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8'))['mods']


def milhar(n, idioma):
    return u'{:,}'.format(n).replace(u',', u'.' if idioma == 'pt' else u',')


def faixa_wh(mod, idioma):
    """Faixa que fica logo abaixo do card do mod: usuários, estrelas e versão."""
    c, L = COR_WH, TXT_WH[idioma]
    det, meta = mod['details'], mod['metadata']
    votos = det.get('ratingBreakdown') or [0] * 5
    n = sum(votos)
    media = sum((i + 1) * v for i, v in enumerate(votos)) / float(n) if n else 0.0

    estrelas = []
    for i in range(5):
        x = 330 + i * 26
        cheio = max(0.0, min(1.0, media - i))
        d = (u'M%.1f 22 L%.1f 30.5 L%.1f 31.2 L%.1f 37 L%.1f 46 L%.1f 41.3 L%.1f 46 L%.1f 37 L%.1f 31.2 L%.1f 30.5 Z'
             % (x + 10, x + 12.9, x + 20, x + 14.7, x + 16.2, x + 10, x + 3.8, x + 5.3, x, x + 7.1))
        estrelas.append(u'<clipPath id="e%d"><rect x="%.1f" y="18" width="%.1f" height="32"/></clipPath>'
                        u'<path d="%s" fill="%s" opacity=".22"/><path d="%s" fill="%s" clip-path="url(#e%d)"/>'
                        % (i, x, 20 * cheio, d, c['mut'], d, c['star'], i))
    if n:
        nota = u'%s · %d %s' % ((u'%.1f' % media).replace(u'.', L['dec']), n, L['aval'][n != 1])
    else:
        nota = L['sem']

    users = milhar(det.get('users', 0), idioma)
    return u'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 68" width="1000" height="68" role="img" aria-label="%(alt)s">
  <title>%(nome)s no Windhawk</title>
  <style>
    .n { font-family: %(SANS)s; font-size: 30px; font-weight: 800; fill: %(ink)s; letter-spacing: -.5px; }
    .f { font-family: %(SANS)s; font-size: 14.5px; fill: %(dim)s; }
    .m { font-family: %(MONO)s; font-size: 10.5px; letter-spacing: 1.4px; fill: %(mut)s; }
  </style>
  <rect x=".5" y=".5" width="999" height="67" fill="%(bg)s" stroke="%(acc)s" stroke-opacity=".35"/>
  <text x="28" y="45" class="n">%(users)s</text>
  <text x="%(ux).1f" y="44" class="f">%(lu)s</text>
  %(EST)s
  <text x="470" y="40" class="f">%(nota)s</text>
  <text x="972" y="39" class="m" text-anchor="end">%(versao)s</text>
</svg>
''' % dict(SANS=SANS, MONO=MONO, nome=escape(meta.get('name', '')), users=users, lu=L['users'],
           ux=36 + len(users) * 17.5, EST=u''.join(estrelas), nota=nota,
           versao=L['versao'] % meta.get('version', u'?'),
           alt=u'%s %s, %s' % (users, L['users'], nota), **c)


def atualiza_windhawk():
    # se o catálogo falhar, os números do GitHub seguem sendo publicados
    try:
        mods = catalogo_wh()
    except Exception as e:
        print('::warning::catálogo do Windhawk indisponível: %s' % e)
        return
    for mid in MODS_WH:
        if mid not in mods:
            print('::warning::%s ainda não está no catálogo do Windhawk' % mid)
            continue
        for idioma in ('pt', 'en'):
            io.open(destino(idioma, 'wh-%s.svg' % mid), 'w', encoding='utf-8', newline='\n').write(
                faixa_wh(mods[mid], idioma))
        det = mods[mid]['details']
        print('windhawk %s: %d usuarios | nota %s | %d avaliacoes'
              % (mid, det.get('users', 0), det.get('rating'), det.get('ratingUsers', 0)))


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

    atualiza_windhawk()


if __name__ == '__main__':
    main()
