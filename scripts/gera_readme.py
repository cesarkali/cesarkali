# -*- coding: utf-8 -*-
"""Monta o README.md com os dois idiomas, cada um num <details> do acordeão.

Os números do texto (projetos, meses, contribuições, dias, privadas) e a ordem
dos mods do Windhawk vêm de scripts/numeros.json, que atualiza_numeros.py grava
todo dia. O workflow roda os dois em sequência, então o README nunca fica
contando um número que as imagens já deixaram para trás.

O <picture> tem de caber numa linha só: quebrado em várias, o parser de markdown
do GitHub descarta o <source> e o tema escuro nunca carrega.

    python scripts/gera_readme.py
"""
import io, json, os

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NUMEROS = os.path.join(RAIZ, 'scripts', 'numeros.json')


def pic(base, alt, idioma, url=None, v=u'hub'):
    pasta = u'assets' if idioma == 'pt' else u'assets/en'
    p = (u'<picture><source media="(prefers-color-scheme: dark)" srcset="%s/%s-dark.svg?v=%s">'
         u'<img src="%s/%s-light.svg?v=%s" width="100%%" alt="%s"></picture>' % (pasta, base, v, pasta, base, v, alt))
    return (u'<a href="%s">%s</a>' % (url, p)) if url else p


def badge(rotulo, url, logo, cor):
    return (u'<a href="%s"><img src="https://img.shields.io/badge/%s-15161A?style=flat-square&logo=%s&logoColor=%s" alt="%s"></a>'
            % (url, rotulo, logo, cor, rotulo))


BADGES = u'\n  '.join([
    badge(u'SITE',      u'https://www.caliberda.com.br',            u'vercel',    u'7D8DFF'),
    badge(u'PORTFÓLIO', u'https://portifolio.caliberda.com.br',     u'polywork',  u'7D8DFF'),
    badge(u'LINKEDIN',  u'https://linkedin.com/in/hxtdll',          u'linkedin',  u'1E90C8'),
    badge(u'EMAIL',     u'mailto:julio@caliberda.com.br',           u'maildotru', u'F08E71'),
    badge(u'INSTAGRAM', u'https://instagram.com/cesar.kali',        u'instagram', u'E4749B'),
    badge(u'YOUTUBE',   u'https://www.youtube.com/@hotdorgs',       u'youtube',   u'E85D5D'),
    badge(u'DISCORD',   u'https://discord.gg/e6VkayX4nG',           u'discord',   u'8FA0F0'),
    badge(u'STEAM',     u'https://steamcommunity.com/id/hotdorgs/', u'steam',     u'8FD8F2'),
])

VISITAS = (u'<img src="https://komarev.com/ghpvc/?username=cesarkali&label=%s&color=15161A&style=flat-square" alt="%s">')

RETRATO = (u'<picture><source media="(max-width: 640px)" srcset="assets/retrato-m.svg?v=wh">'
           u'<source media="(prefers-color-scheme: dark)" srcset="assets/retrato-dark.svg?v=hub">'
           u'<img src="assets/retrato-light.svg?v=hub" align="right" alt="Júlio Caliberda"></picture>')

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


def bloco(idioma, conteudo, aberto):
    """<details> com name igual formam um acordeão exclusivo no próprio HTML:
    abrir um fecha o outro, sem JavaScript. O GitHub preserva o atributo."""
    rotulo = (u'🇧🇷 <b>Português</b>' if idioma == 'pt' else u'🇺🇸 <b>English</b>')
    return (u'<details name="idioma"%s>\n'
            u'<summary>&nbsp;%s &nbsp;·&nbsp;</summary>\n\n'
            u'%s\n\n</details>' % (u' open' if aberto else u'', rotulo, conteudo))


TXT = {
 'pt': dict(
   visitas=u'VISITAS',
   h_quem=u'Não sou desenvolvedor',
   p1=u'E não vou fingir que sou. Não sei código o suficiente para me chamar disso.',
   p2=u'O que eu faço é outra coisa: descobrir o que precisa existir, entender **por que** precisa existir, e conduzir a IA até aquilo virar produto de verdade. Que abre, que funciona, que alguém usa todo dia sem saber quem fez.',
   p3=u'De dia sou **Product Analyst na Bitz Softwares**, ouvindo o problema de quem sofre com ele antes de qualquer linha ser escrita. Este perfil é o que acontece quando eu aponto o mesmo olhar para as minhas ideias, sem ninguém ter pedido.',
   p4=u'Nada aqui saiu de curso, bootcamp ou roadmap. Saiu de *"e se desse pra fazer isso?"* seguido de muita teimosia.',
   c1t=u'O que eu faço', c1=u'Direção de produto, análise de sistema e prompt. Descubro o que construir, explico com precisão e leio o resultado sabendo quando está errado.',
   c2t=u'O que está no ar', c2=u'%(repos)d projetos em %(meses)d meses. Um SaaS financeiro com app nativo, dois mods de Minecraft, três mods do Windhawk, extensão publicada na Chrome Web Store e sites de cliente rodando.',
   c3t=u'Como eu insisto', c3=u'%(contrib)d contribuições em %(dias)d dias diferentes, %(privadas)d delas em repositório privado. Nenhum projeto aqui funcionou de primeira.',
   h_esc=u'Eu não escrevo o código. Escrevo o pedido.',
   s_esc=u'O que eu faço não cabe numa linha de commit. Dá para medir pelo tamanho do que precisa ser decidido e mantido de pé.',
   h_dest=u'Em destaque',
   wh_alt=u'%s no Windhawk: usuários e avaliações',
   wh_nota=u'Faço parte de quem cria mods para o <a href="https://windhawk.net">Windhawk</a>. Os três estão publicados na loja: o terceiro, o <a href="https://windhawk.net/mods/windows-terminal-start-minimized">Windows Terminal iniciar minimizado</a>, é um menor, que abre o Windows Terminal já minimizado no logon. <a href="https://github.com/cesarkali/windhawk-mods-showcase">Veja todos juntos</a>.',
   s_dest=u'Clique em qualquer um para abrir. O INSONE ainda não tem página: está sendo escrito. Os mods do Windhawk têm código aberto, como todo mod de lá. Os outros quatro têm o código fechado.',
   h_port=u'Meu portfólio',
   h_resto=u'O resto',
   t_jogar=u'Para jogar', t_ferr=u'Ferramentas que eu uso todo dia',
   t_mine=u'Minecraft', t_prod=u'Produtos e clientes',
   nota=u'Onde não tem link, o código é privado ou o projeto ainda não está no ar. <b>OtimizaDorgs</b>, otimizador de PC para jogos com tweaks reversíveis, é um deles.',
   det=u'e mais uns quantos experimentos',
   det_txt=u'Nem tudo vira produto, e tudo bem. Vários nasceram num fim de semana só para responder uma pergunta: **Bitz Loader** e **Docs Bitz**, internos da BitzSoftwares · **Controle de Pedidos** em Next.js sobre a API Eatz · **IA ou Humano**, um teste pequeno sobre quem escreveu o texto.\n\nE outros tantos que ficaram pelo caminho, porque parte de construir é aceitar que nem toda ideia merece continuar.',
   h_num=u'Os números, sem maquiagem',
   h_fim=u'Se você chegou até aqui',
   f1=u'Se alguma dessas coisas te deu vontade de construir a sua, me chama. Gosto muito mais de conversar sobre a ideia do que sobre a ferramenta.',
   f2=u'E se você também acha que não sabe o suficiente para começar: **eu também achava.**',
   jogar=[(u'Kessler Cascade', u'https://kessler.caliberda.com.br', u'você não tem armas: captura o que atiram em você e devolve'),
          (u'AFÓTICA', u'https://afotica.caliberda.com.br', u'o som é a sua visão, e denuncia onde você está'),
          (u'Neon Strike', u'https://neonstrike.caliberda.com.br', u'arcade cyberpunk com trilha gerada no navegador'),
          (u'HORIZONTE', u'https://fable-airplane.vercel.app', u'voo 3D com 26 aeroportos brasileiros reais'),
          (u'CS2 Mix', u'https://www.caliberda.com.br/cs2mix', u'times equilibrados pelo rating real do Leetify')],
   ferr=[(u'FlowVoice', u'https://flowvoice.caliberda.com.br/', u'ditado por voz com IA em qualquer campo, offline se quiser', u'https://github.com/cesarkali/Flow-Voice', u'código'),
         (u'Semantic Tab Grouper', u'https://stg.caliberda.com.br/', u'agrupa abas pelo assunto, com IA rodando no seu navegador', u'https://github.com/cesarkali/Semantic-Tab-Grouper', u'código'),
         (u'CSGO-SKINS Inspector', u'https://csskins.caliberda.com.br/', u'inspeciona a skin no CS2 e mostra o preço da Steam direto no site', None, None),
         (u'PMTT', u'https://pmtt.caliberda.com.br', u'prova o trabalho invisível que ninguém vê você fazendo', None, None),
         (u'CNPJ API', u'https://ccnpj.caliberda.com.br/', u'dados de qualquer empresa brasileira pelo CNPJ', u'https://github.com/cesarkali/ccnpj', u'código')],
   mine=[(u'AllayFriend', u'https://allayfriend.caliberda.com.br', u'companheiro de IA rodando dentro do jogo'),
         (u'INSONE, Noites Devidas', None, u'terror com narrativa própria, em construção'),
         (u'Modpack HotDorgs', u'https://www.caliberda.com.br/minecraft', u'ajustado no osso para estabilidade de tick')],
   prod=[(u'Financial Kali', u'https://kali.caliberda.com.br', u'gestão financeira multi-empresa com IA'),
         (u'Modal de Check-in', u'https://modal.caliberda.com.br', u'check-in de hotel sem atrito'),
         (u'Petshop 4i', u'https://petshop-4i.vercel.app', u'site e loja de um petshop real'),
         (u'Eatz · BitzWay', None, u'autoatendimento de restaurante e portal de reservas'),
         (u'Karol ZK', u'https://karolzk.com.br', u'plataformas de creator, com [Isa Titon](https://isatiton.com.br)')],
 ),
 'en': dict(
   visitas=u'VISITS',
   h_quem=u'I am not a developer',
   p1=u'And I will not pretend to be. I do not know enough code to call myself that.',
   p2=u'What I do is something else: figuring out what needs to exist, understanding **why** it needs to exist, and steering AI until it becomes a real product. One that opens, that works, that someone uses every day without knowing who made it.',
   p3=u'By day I am a **Product Analyst at Bitz Softwares**, listening to the problem of whoever is suffering with it before a single line gets written. This profile is what happens when I point that same attention at my own ideas, with nobody asking.',
   p4=u'None of this came from a course, a bootcamp or a roadmap. It came from *"what if this could be done?"* followed by a lot of stubbornness.',
   c1t=u'What I bring', c1=u'Product direction, systems analysis and prompting. I find what is worth building, explain it precisely, and read the result knowing when it is wrong.',
   c2t=u'What is live', c2=u'%(repos)d projects in %(meses)d months. A finance SaaS with a native app, two Minecraft mods, three Windhawk mods, an extension published on the Chrome Web Store and client sites running.',
   c3t=u'How I keep at it', c3=u'%(contrib)d contributions across %(dias)d different days, %(privadas)d of them in private repos. Nothing here worked on the first try.',
   h_esc=u'I do not write the code. I write the ask.',
   s_esc=u'What I do does not fit in a commit line. You can measure it by the size of what has to be decided and kept standing.',
   h_dest=u'Highlights',
   wh_alt=u'%s on Windhawk: users and ratings',
   wh_nota=u'I am one of the people building mods for <a href="https://windhawk.net">Windhawk</a>. All three are published on the store: the third, <a href="https://windhawk.net/mods/windows-terminal-start-minimized">Windows Terminal Start Minimized</a>, is a small one that opens Windows Terminal minimized at sign-in. <a href="https://github.com/cesarkali/windhawk-mods-showcase">See all of them together</a>.',
   s_dest=u'Click any of them to open. INSONE has no page yet: it is still being written. The Windhawk mods are open source, like every mod there. The other four are closed source.',
   h_port=u'My portfolio',
   h_resto=u'The rest',
   t_jogar=u'To play', t_ferr=u'Tools I use every day',
   t_mine=u'Minecraft', t_prod=u'Products and clients',
   nota=u'Where there is no link, the code is private or the project is not live yet. <b>OtimizaDorgs</b>, a PC optimizer for games with reversible tweaks, is one of them.',
   det=u'and a few more experiments',
   det_txt=u'Not everything becomes a product, and that is fine. Several were born over a weekend just to answer one question: **Bitz Loader** and **Docs Bitz**, internal to BitzSoftwares · **Controle de Pedidos** in Next.js on the Eatz API · **IA ou Humano**, a small test about who wrote the text.\n\nAnd plenty of others left behind, because part of building is accepting that not every idea deserves to continue.',
   h_num=u'The numbers, unretouched',
   h_fim=u'If you made it this far',
   f1=u'If any of this made you want to build your own, reach out. I enjoy talking about the idea far more than about the tool.',
   f2=u'And if you also think you do not know enough to start: **I thought that too.**',
   jogar=[(u'Kessler Cascade', u'https://kessler.caliberda.com.br', u'you have no weapons: you catch what is fired at you and throw it back'),
          (u'AFÓTICA', u'https://afotica.caliberda.com.br', u'sound is your sight, and it gives away where you are'),
          (u'Neon Strike', u'https://neonstrike.caliberda.com.br', u'cyberpunk arcade with a soundtrack generated in the browser'),
          (u'HORIZONTE', u'https://fable-airplane.vercel.app', u'3D flight with 26 real Brazilian airports'),
          (u'CS2 Mix', u'https://www.caliberda.com.br/cs2mix', u'balanced teams from real Leetify ratings')],
   ferr=[(u'FlowVoice', u'https://flowvoice.caliberda.com.br/', u'AI voice dictation into any field, offline if you want', u'https://github.com/cesarkali/Flow-Voice', u'code'),
         (u'Semantic Tab Grouper', u'https://stg.caliberda.com.br/', u'groups tabs by subject, with AI running in your browser', u'https://github.com/cesarkali/Semantic-Tab-Grouper', u'code'),
         (u'CSGO-SKINS Inspector', u'https://csskins.caliberda.com.br/', u'inspects the skin in CS2 and shows the Steam price on the site', None, None),
         (u'PMTT', u'https://pmtt.caliberda.com.br', u'proves the invisible work nobody sees you doing', None, None),
         (u'CNPJ API', u'https://ccnpj.caliberda.com.br/', u'data on any Brazilian company from its tax ID', u'https://github.com/cesarkali/ccnpj', u'code')],
   mine=[(u'AllayFriend', u'https://allayfriend.caliberda.com.br', u'an AI companion running inside the game'),
         (u'INSONE, Nights Owed', None, u'horror with an original story, in progress'),
         (u'Modpack HotDorgs', u'https://www.caliberda.com.br/minecraft', u'tuned to the bone for tick stability')],
   prod=[(u'Financial Kali', u'https://kali.caliberda.com.br', u'multi-company finance management with AI'),
         (u'Modal de Check-in', u'https://modal.caliberda.com.br', u'frictionless hotel check-in'),
         (u'Petshop 4i', u'https://petshop-4i.vercel.app', u'site and shop for a real pet store'),
         (u'Eatz · BitzWay', None, u'restaurant self-service and a booking portal'),
         (u'Karol ZK', u'https://karolzk.com.br', u'creator platforms, with [Isa Titon](https://isatiton.com.br)')],
 ),
}


def lista(itens):
    linhas = []
    for it in itens:
        nome, url, desc = it[0], it[1], it[2]
        titulo = u'**[%s](%s)**' % (nome, url) if url else u'**%s**' % nome
        extra = u''
        if len(it) > 3 and it[3]:
            extra = u' · [%s](%s)' % (it[4], it[3])
        linhas.append(u'- %s · %s%s' % (titulo, desc, extra))
    return u'\n'.join(linhas)


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
    P = lambda b, a, u=None, v=u'hub': pic(b, a, idioma, u, v)

    return u'''<div align="center">

%(HERO)s

</div>

<div align="center">
  %(BADGES)s
</div>

<div align="center">
  %(VISITAS)s
</div>

<br>

%(RETRATO)s

### %(h_quem)s

%(p1)s

%(p2)s

%(p3)s

%(p4)s

<br clear="right">

<table width="100%%">
<tr>
<td width="34%%" valign="top">

**%(c1t)s**

%(c1)s

</td>
<td width="33%%" valign="top">

**%(c2t)s**

%(C2)s

</td>
<td width="33%%" valign="top">

**%(c3t)s**

%(C3)s

</td>
</tr>
</table>

<br>

### %(h_esc)s

<sub>%(s_esc)s</sub>

%(ESCOPO)s

<br>

### %(h_dest)s

%(WINDHAWK)s

<sub>%(wh_nota)s</sub>

%(DFIN)s

%(DALL)s

%(DINS)s

%(DQT)s

<sub>%(s_dest)s</sub>

<br>

### %(h_port)s

%(PORT)s

<br>

### %(h_resto)s

<table width="100%%">
<tr><td valign="top" width="50%%">

**%(t_jogar)s**

%(JOGAR)s

</td><td valign="top" width="50%%">

**%(t_ferr)s**

%(FERR)s

</td></tr>
<tr><td valign="top">

**%(t_mine)s**

%(MINE)s

</td><td valign="top">

**%(t_prod)s**

%(PROD)s

</td></tr>
</table>

<sub>%(nota)s</sub>

<details>
<summary>%(det)s</summary>

<br>

%(det_txt)s

</details>

<br>

### %(h_num)s

%(NUMEROS)s

%(HEATMAP)s

<br>

### %(h_fim)s

%(f1)s

%(f2)s

<div align="center">
<sub><a href="https://www.caliberda.com.br">caliberda.com.br</a></sub>
</div>
''' % dict(
    BADGES=BADGES,
    VISITAS=VISITAS % (L['visitas'], L['visitas']),
    RETRATO=RETRATO,
    HERO=P('hero', u'Júlio Caliberda', v=u'pa'),
    C2=L['c2'] % n, C3=L['c3'] % n,
    ESCOPO=P('escopo', u'INSONE'),
    WINDHAWK=windhawk(idioma, L, n.get('windhawk', {})),
    DFIN=P('d-financial', u'Financial Kali', u'https://kali.caliberda.com.br'),
    DALL=P('d-allayfriend', u'AllayFriend', u'https://allayfriend.caliberda.com.br'),
    DINS=P('d-insone', u'INSONE'),
    DQT=P('d-qt', u'Quatro Temperamentos', u'https://qt.caliberda.com.br/'),
    PORT=P('portfolio', u'Portfolio', u'https://portifolio.caliberda.com.br/'),
    NUMEROS=P('numeros', u'%(repos)d / %(contrib)d / %(dias)d / %(privadas)d' % n, v=u'wh'),
    HEATMAP=P('heatmap', u'Contribution map'),
    JOGAR=lista(L['jogar']), FERR=lista(L['ferr']),
    MINE=lista(L['mine']), PROD=lista(L['prod']),
    **{k: v for k, v in L.items() if isinstance(v, str) and k not in ('c2', 'c3')})


if __name__ == '__main__':
    n = json.load(io.open(NUMEROS, encoding='utf-8'))
    # inglês primeiro e fechado, para os dois seletores ficarem juntos no topo
    doc = u'%s\n\n%s\n' % (bloco('en', monta('en', n), False),
                           bloco('pt', monta('pt', n), True))
    io.open(os.path.join(RAIZ, 'README.md'), 'w', encoding='utf-8', newline='\n').write(doc)
    print('README.md gerado: %(repos)d projetos, %(meses)d meses, %(contrib)d contribuicoes, '
          '%(dias)d dias, %(privadas)d privadas' % n)
