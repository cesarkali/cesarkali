# -*- coding: utf-8 -*-
"""Monta o README.md com os dois idiomas, cada um num <details> do acordeão.

Os números do texto e a ordem dos mods do Windhawk vêm de scripts/numeros.json,
que atualiza_numeros.py grava todo dia. O workflow roda os dois em sequência,
então o README nunca fica contando um número que as imagens já deixaram para trás.

O <picture> tem de caber numa linha só: quebrado em várias, o parser de markdown
do GitHub descarta o <source> e o tema escuro nunca carrega.

    python scripts/gera_readme.py
"""
import io, json, os

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NUMEROS = os.path.join(RAIZ, 'scripts', 'numeros.json')

SPONSOR = u'https://github.com/sponsors/cesarkali'
PIX     = u'https://livepix.gg/caliberda'
VITRINE = u'https://github.com/cesarkali/windhawk-mods-showcase'
ISSUES  = u'https://github.com/ramensoftware/windhawk-mods/issues'
# o Windows não desenha emoji de bandeira (vira "BR" em texto): a bandeira é SVG
BR = u'<img src="assets/idioma/br.svg" height="13" alt="Brasil">'


def pic(base, alt, idioma, url=None, v=u'hub'):
    pasta = u'assets' if idioma == 'pt' else u'assets/en'
    p = (u'<picture><source media="(prefers-color-scheme: dark)" srcset="%s/%s-dark.svg?v=%s">'
         u'<img src="%s/%s-light.svg?v=%s" width="100%%" alt="%s"></picture>' % (pasta, base, v, pasta, base, v, alt))
    return (u'<a href="%s">%s</a>' % (url, p)) if url else p


def badge(rotulo, url, logo, cor, estilo=u'flat-square'):
    return (u'<a href="%s"><img src="https://img.shields.io/badge/%s-15161A?style=%s&logo=%s&logoColor=%s" alt="%s"></a>'
            % (url, rotulo, estilo, logo, cor, rotulo))


BADGES = u'\n  '.join([
    badge(u'SITE',      u'https://www.caliberda.com.br',        u'vercel',    u'7D8DFF'),
    badge(u'PORTFÓLIO', u'https://portifolio.caliberda.com.br', u'polywork',  u'7D8DFF'),
    badge(u'LINKEDIN',  u'https://linkedin.com/in/hxtdll',      u'linkedin',  u'1E90C8'),
    badge(u'EMAIL',     u'mailto:julio@caliberda.com.br',       u'maildotru', u'F08E71'),
    badge(u'INSTAGRAM', u'https://instagram.com/cesar.kali',    u'instagram', u'E4749B'),
])

VISITAS = (u'<img src="https://komarev.com/ghpvc/?username=cesarkali&label=%s&color=15161A&style=flat-square" alt="%s">')

# Mods do Windhawk em destaque. Saem ordenados por quem tem mais gente usando,
# pelo catálogo do Windhawk; "v" é o cache do card (mude ao trocar o desenho).
WINDHAWK = [
    dict(id=u'mac-island-dock', nome=u'Mac Island &amp; Dock', card=u'd-island', v=u'wh2',
         midia=u'assets/windhawk-island-2-1.webp',
         alt={'en': u'Mac Island &amp; Dock running: the island opens from its line, a timer runs, then the media panel and its mixer open',
              'pt': u'Mac Island &amp; Dock funcionando: a ilha se abre da linha, um timer corre e depois abrem o painel de mídia e o mixer'}),
    dict(id=u'alt-tab-flip-3d', nome=u'Alt+Tab Flip 3D', card=u'd-windhawk', v=u'wh',
         midia=u'assets/windhawk-flip3d.gif',
         alt={'en': u'Alt+Tab Flip 3D running: windows fly into a 3D stack',
              'pt': u'Alt+Tab Flip 3D funcionando: as janelas voam para uma pilha 3D'}),
]

TXT = {
 'pt': dict(
   resumo=u'Português · original, feito no Brasil',
   visitas=u'VISITAS',
   gancho=u'%(total)s pessoas usam os meus mods do Windhawk',
   sub=u'Feitos no Brasil %s · gratuitos, de código aberto e revisados pelo Windhawk antes de cada versão.' % BR,
   quem=u'Júlio Caliberda · Product Analyst · Pato Branco, PR %s' % BR,
   p1=u'Sou Product Analyst na **Bitz Softwares**: meu trabalho é entender o problema antes de qualquer linha de código. Nos meus projetos uso o mesmo método. Eu defino o que precisa existir, como deve funcionar e quando está pronto, e a IA escreve o código.',
   h_mods=u'Mods do Windhawk',
   wh_alt=u'%s no Windhawk: usuários e avaliações',
   terminal=u'O terceiro, o [Windows Terminal iniciar minimizado](https://windhawk.net/mods/windows-terminal-start-minimized), é um menor: abre o Windows Terminal já minimizado no logon. [Os três juntos, numa página só](%s).' % VITRINE,
   card=u'Os mods do Windhawk em números',
   apoio=u'**Os mods são de graça e vão continuar assim.**<br>Se algum deixou o seu Windows melhor e você quiser dar uma força:',
   apoie=u'APOIE',
   issues=u'Achou um bug ou tem uma ideia? Abra uma [issue no repositório oficial](%s), assim nada se perde.' % ISSUES,
   h_proj=u'Outros projetos', cab=(u'Projeto', u'O que é'), cod=u'código',
   projetos=[(u'Financial Kali', u'https://kali.caliberda.com.br', u'gestão financeira multiempresa, com assistente de IA, na web e em app nativo', None),
             (u'FlowVoice', u'https://flowvoice.caliberda.com.br/', u'ditado por voz com IA em qualquer campo do Windows, offline se quiser · 15 versões publicadas', u'https://github.com/cesarkali/Flow-Voice'),
             (u'Semantic Tab Grouper', u'https://chromewebstore.google.com/detail/semantic-tab-grouper/illkdfiegklhcjogdhplihjekfjdocgk', u'extensão do Chrome que agrupa abas pelo assunto, com a IA rodando no próprio navegador', u'https://github.com/cesarkali/Semantic-Tab-Grouper'),
             (u'PMTT', u'https://pmtt.caliberda.com.br', u'registra o trabalho invisível de quem faz produto', u'https://github.com/cesarkali/Product-Manager-Timer-Tracker'),
             (u'Os Quatro Temperamentos', u'https://qt.caliberda.com.br/', u'inventário de autoconhecimento com 128 perguntas, tudo no navegador', None),
             (u'CNPJ API', u'https://ccnpj.caliberda.com.br/', u'dados de qualquer empresa brasileira pelo CNPJ', u'https://github.com/cesarkali/ccnpj')],
   h_jogos=u'Jogos e experimentos',
   jogos=[(u'Kessler Cascade', u'https://kessler.caliberda.com.br', u'você não tem armas: captura o que atiram em você e devolve'),
          (u'AFÓTICA', u'https://afotica.caliberda.com.br', u'o som é a sua visão, e denuncia onde você está'),
          (u'HORIZONTE', u'https://fable-airplane.vercel.app', u'voo 3D com 26 aeroportos brasileiros reais'),
          (u'Neon Strike', u'https://neonstrike.caliberda.com.br', u'arcade cyberpunk com trilha gerada no navegador'),
          (u'CS2 Mix', u'https://www.caliberda.com.br/cs2mix', u'times equilibrados pelo rating real do Leetify'),
          (u'AllayFriend', u'https://allayfriend.caliberda.com.br', u'mod de Minecraft com um companheiro de IA rodando dentro do jogo'),
          (u'INSONE, Noites Devidas', None, u'mod de terror para Minecraft com narrativa própria, em construção')],
   h_cli=u'Clientes',
   clientes=u'Sites para quem cria conteúdo e para negócios locais: [Isa Titon](https://isatiton.com.br), [Karol ZK](https://karolzk.com.br) e o [Petshop 4i](https://petshop-4i.vercel.app).',
   h_num=u'Os números',
   contato=u'Para conversar: [julio@caliberda.com.br](mailto:julio@caliberda.com.br) · [LinkedIn](https://linkedin.com/in/hxtdll) · [caliberda.com.br](https://www.caliberda.com.br)',
 ),
 'en': dict(
   resumo=u'English · read this profile in English',
   visitas=u'VISITS',
   gancho=u'%(total)s people use my Windhawk mods',
   sub=u'Made in Brazil %s · free, open source, and reviewed by Windhawk before every release.' % BR,
   quem=u'Júlio Caliberda · Product Analyst · Pato Branco, Brazil %s' % BR,
   p1=u'I am a Product Analyst at **Bitz Softwares**: my job is to understand the problem before any line of code. My own projects use the same method. I define what needs to exist, how it should work and when it is done, and AI writes the code.',
   h_mods=u'Windhawk mods',
   wh_alt=u'%s on Windhawk: users and ratings',
   terminal=u'The third one, [Windows Terminal Start Minimized](https://windhawk.net/mods/windows-terminal-start-minimized), is a small one: it opens Windows Terminal minimized at sign-in. [All three together on one page](%s).' % VITRINE,
   card=u'The Windhawk mods in numbers',
   apoio=u'**The mods are free and will stay free.**<br>If one of them made your Windows nicer and you want to help:',
   apoie=u'SPONSOR',
   issues=u'Found a bug or have an idea? Open an [issue in the official repo](%s), so nothing gets lost.' % ISSUES,
   h_proj=u'Other projects', cab=(u'Project', u'What it is'), cod=u'code',
   projetos=[(u'Financial Kali', u'https://kali.caliberda.com.br', u'multi-company finance management with an AI assistant, on the web and as a native app', None),
             (u'FlowVoice', u'https://flowvoice.caliberda.com.br/', u'AI voice dictation into any Windows field, offline if you want · 15 releases', u'https://github.com/cesarkali/Flow-Voice'),
             (u'Semantic Tab Grouper', u'https://chromewebstore.google.com/detail/semantic-tab-grouper/illkdfiegklhcjogdhplihjekfjdocgk', u'Chrome extension that groups tabs by subject, with the AI running in the browser itself', u'https://github.com/cesarkali/Semantic-Tab-Grouper'),
             (u'PMTT', u'https://pmtt.caliberda.com.br', u'records the invisible work of people who build products', u'https://github.com/cesarkali/Product-Manager-Timer-Tracker'),
             (u'The Four Temperaments', u'https://qt.caliberda.com.br/', u'a self-knowledge inventory with 128 questions, all in the browser', None),
             (u'CNPJ API', u'https://ccnpj.caliberda.com.br/', u'data on any Brazilian company from its tax ID', u'https://github.com/cesarkali/ccnpj')],
   h_jogos=u'Games and experiments',
   jogos=[(u'Kessler Cascade', u'https://kessler.caliberda.com.br', u'you have no weapons: you catch what is fired at you and throw it back'),
          (u'AFÓTICA', u'https://afotica.caliberda.com.br', u'sound is your sight, and it gives away where you are'),
          (u'HORIZONTE', u'https://fable-airplane.vercel.app', u'3D flight with 26 real Brazilian airports'),
          (u'Neon Strike', u'https://neonstrike.caliberda.com.br', u'cyberpunk arcade with a soundtrack generated in the browser'),
          (u'CS2 Mix', u'https://www.caliberda.com.br/cs2mix', u'balanced teams from real Leetify ratings'),
          (u'AllayFriend', u'https://allayfriend.caliberda.com.br', u'Minecraft mod with an AI companion running inside the game'),
          (u'INSONE, Nights Owed', None, u'horror mod for Minecraft with an original story, in progress')],
   h_cli=u'Clients',
   clientes=u'Sites for creators and local businesses: [Isa Titon](https://isatiton.com.br), [Karol ZK](https://karolzk.com.br) and [Petshop 4i](https://petshop-4i.vercel.app).',
   h_num=u'The numbers',
   contato=u'Get in touch: [julio@caliberda.com.br](mailto:julio@caliberda.com.br) · [LinkedIn](https://linkedin.com/in/hxtdll) · [caliberda.com.br](https://www.caliberda.com.br)',
 ),
}


def milhar(v, idioma):
    return u'{:,}'.format(v).replace(u',', u'.' if idioma == 'pt' else u',')


def bloco(idioma, conteudo, aberto):
    """<details> com name igual formam um acordeão exclusivo no próprio HTML:
    abrir um fecha o outro, sem JavaScript. O GitHub preserva o atributo. O
    resumo é um botão com a bandeira desenhada."""
    nome = u'pt' if idioma == 'pt' else u'en'
    resumo = (u'<summary><picture><source media="(prefers-color-scheme: dark)" srcset="assets/idioma/%s-dark.svg">'
              u'<img src="assets/idioma/%s-light.svg" height="38" alt="%s"></picture></summary>'
              % (nome, nome, TXT[idioma]['resumo']))
    return u'<details name="idioma"%s>\n%s\n\n%s\n\n</details>' % (u' open' if aberto else u'', resumo, conteudo)


def lista(itens):
    return u'\n'.join(u'- %s · %s' % (u'**[%s](%s)**' % (nome, url) if url else u'**%s**' % nome, desc)
                      for nome, url, desc in itens)


def tabela(L):
    linhas = [u'| **[%s](%s)** | %s%s |' % (nome, url, desc, u' · [%s](%s)' % (L['cod'], cod) if cod else u'')
              for nome, url, desc, cod in L['projetos']]
    return u'| %s | %s |\n|---|---|\n%s' % (L['cab'][0], L['cab'][1], u'\n'.join(linhas))


def windhawk(idioma, L, usuarios):
    """Card, faixa de usuários e animação de cada mod, do mais usado para o menos.
    Empate ou mod fora do catálogo mantém a ordem da lista."""
    pasta = u'assets' if idioma == 'pt' else u'assets/en'
    ordem = sorted(WINDHAWK, key=lambda m: -usuarios.get(m['id'], 0))
    partes = []
    for m in ordem:
        url = u'https://windhawk.net/mods/%s' % m['id']
        partes.append(u'%s<br>\n<a href="%s"><img src="%s/wh-%s.svg" width="100%%" alt="%s"></a>\n\n'
                      u'<a href="%s"><img src="%s" width="100%%" alt="%s"></a>'
                      % (pic(m['card'], m['nome'], idioma, url, m['v']), url, pasta, m['id'], L['wh_alt'] % m['nome'],
                         url, m['midia'], m['alt'][idioma]))
    return u'\n\n'.join(partes)


def monta(idioma, n):
    L = TXT[idioma]
    pasta = u'assets' if idioma == 'pt' else u'assets/en'
    total = n.get('mods', {}).get('usuarios') or sum(n.get('windhawk', {}).values())
    apoio = (badge(L['apoie'], SPONSOR, u'githubsponsors', u'EA4AAA', u'for-the-badge') + u' '
             + badge(u'PIX', PIX, u'pix', u'32BCAD', u'for-the-badge'))
    return u'\n\n'.join([
        u'<div align="center">\n\n%s\n\n</div>' % pic('hero', u'Júlio Caliberda', idioma, v=u'pa'),
        u'<div align="center">\n  %s\n</div>' % BADGES,
        u'<div align="center">\n  %s\n</div>' % (VISITAS % (L['visitas'], L['visitas'])),
        u'<h3 align="center">%s</h3>' % (L['gancho'] % dict(total=milhar(total, idioma))),
        u'<p align="center">%s</p>' % L['sub'],
        u'<br>',
        u'### ' + L['quem'], L['p1'],
        u'<br>',
        u'### ' + L['h_mods'],
        windhawk(idioma, L, n.get('windhawk', {})),
        L['terminal'],
        u'<a href="%s"><img src="%s/mods-windhawk.svg" width="100%%" alt="%s"></a>' % (VITRINE, pasta, L['card']),
        u'<div align="center">\n\n%s\n\n%s\n\n<sub>%s</sub>\n\n</div>' % (L['apoio'], apoio, L['issues']),
        u'<br>',
        u'### ' + L['h_proj'], tabela(L),
        u'<br>',
        u'### ' + L['h_jogos'], lista(L['jogos']),
        u'### ' + L['h_cli'], L['clientes'],
        u'<br>',
        u'### ' + L['h_num'],
        pic('numeros', u'%(repos)d / %(contrib)d / %(dias)d / %(privadas)d' % n, idioma, v=u'wh'),
        pic('heatmap', u'Contribution map', idioma),
        u'<br>',
        L['contato'],
    ]) + u'\n'


if __name__ == '__main__':
    n = json.load(io.open(NUMEROS, encoding='utf-8'))
    # inglês primeiro e fechado: o botão em inglês fica no topo, o português abre sozinho
    doc = u'%s\n\n%s\n' % (bloco('en', monta('en', n), False), bloco('pt', monta('pt', n), True))
    io.open(os.path.join(RAIZ, 'README.md'), 'w', encoding='utf-8', newline='\n').write(doc)
    print('README.md gerado: %(repos)d projetos, %(contrib)d contribuicoes, %(dias)d dias' % n)
