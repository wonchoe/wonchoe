#!/usr/bin/env python3
"""Build four small, self-contained animated illustrations for the README.

These are product previews, not screenshots or interactive UI. Their visual
language follows the public products: cursor packs; YouTube player controls;
Slither's neon spheres/grid; Terra's low-poly terrain, water and village.
Nothing is downloaded at build or display time. CSS also works when an SVG is
embedded as an <img> on GitHub; reduced-motion keeps an intentional still frame.
"""
import math
from pathlib import Path

import typeset as T

ROOT = Path(__file__).resolve().parent.parent
WHITE = "#EDF2FF"
MUTED = "#9DB2D6"
CYAN = "#55DDF5"
PURPLE = "#AB8AFF"


def label(value, x, y, size=14, color=MUTED, role="text", anchor="start"):
    return f'<g fill="{color}">{T.run(role, value, size, x, y, anchor=anchor)}</g>'


def card(name, subtitle, description, accent, action, body, css="", defs="", static=False):
    heading = label(name, 24, 35, 29, WHITE, "display")
    heading += label(subtitle, 25, 57, 15)
    footer = label("PRODUCT PREVIEW" if static else "ANIMATED PREVIEW", 25, 278, 10, MUTED, "mono")
    footer += label(action, 427, 279, 15, accent, "display", "end")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="300" viewBox="0 0 480 300" role="img" aria-labelledby="title desc">
<title id="title">{name} {'still' if static else 'animated'} product preview</title>
<desc id="desc">{description} This is an illustration, not a screenshot. Open the linked product to try it.</desc>
<defs>
  <linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0A1028"/><stop offset="1" stop-color="#111C3E"/></linearGradient>
  <radialGradient id="halo"><stop stop-color="{accent}" stop-opacity=".16"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
  <clipPath id="window"><rect x="24" y="77" width="432" height="170" rx="14"/></clipPath>
  <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="#486088" opacity=".4"/></pattern>
  {defs}
  {T.defs()}
</defs>
<style>
  {'' if static else css}
  @media (prefers-reduced-motion:reduce) {{ .motion {{ animation:none !important }} }}
</style>
<rect x=".5" y=".5" width="479" height="299" rx="20" fill="url(#bg)" stroke="#293759"/>
<ellipse cx="404" cy="109" rx="135" ry="115" fill="url(#halo)"/>
{heading}
<rect x="24" y="77" width="432" height="170" rx="14" fill="#080F25" stroke="#293A5C"/>
<g clip-path="url(#window)">{body}</g>
<path d="M25 257H455" stroke="#26324F"/>
{footer}
<path d="M438 280l8-8m-7 0h7v7" fill="none" stroke="{accent}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''


ARROW = "M0 0 0 39 10 30 18 46 26 42 18 27 32 25Z"
STAR = "M0-22 6-7 22-6 10 5 14 21 0 13-14 21-10 5-22-6-6-7Z"


def cursor_card(static=False):
    T.reset()
    tiles = ""
    for idx, y in enumerate((91, 142, 193)):
        tiles += f'<rect x="39" y="{y}" width="62" height="42" rx="9" fill="#152142" stroke="#354B74"/>'
        if idx == 0:
            tiles += f'<g transform="translate(62 {y+7}) scale(.6)"><path d="{ARROW}" fill="{CYAN}" stroke="#DBF8FF" stroke-width="1.5" stroke-linejoin="round"/></g>'
        elif idx == 1:
            tiles += f'<g transform="translate(70 {y+21}) scale(.67)"><path d="{STAR}" fill="#FDD36D" stroke="#FFF0BE" stroke-width="1.5" stroke-linejoin="round"/></g>'
        else:
            tiles += f'<g transform="translate(70 {y+21}) scale(.6)"><path d="M-18-3-17-23-5-13Q0-16 5-13L17-23 18-3Q22 21 0 23-22 21-18-3Z" fill="#F3AADE" stroke="#FFE2F5" stroke-width="1.5"/><path d="M-8 1v4m16-4v4M-3 12q3 4 6 0" stroke="#492651" stroke-width="3" fill="none" stroke-linecap="round"/></g>'
    trail = '<path d="M174 211C168 166 215 104 275 119S386 165 361 195 284 228 243 184" fill="none" stroke="url(#trail)" stroke-width="3" stroke-linecap="round" opacity=".6"/>'
    trail += '<path class="motion trail" d="M174 211C168 166 215 104 275 119S386 165 361 195 284 228 243 184" fill="none" stroke="#ADF2FF" stroke-width="3" stroke-dasharray="7 100" opacity=".65"/>'
    body = f'''<rect x="119" y="77" width="337" height="170" fill="url(#dots)"/>
    <path d="M117 90v144" stroke="#273753"/>
    {tiles}<rect class="motion selection" x="39" y="91" width="62" height="42" rx="9" fill="none" stroke="{CYAN}" stroke-width="2"/>
    {trail}
    <g opacity=".65" fill="#CAA4FF"><path d="M385 111v12m-6-6h12M159 130v8m-4-4h8" stroke="#CAA4FF" stroke-width="1.5"/><circle cx="402" cy="212" r="2"/><circle cx="199" cy="106" r="2"/></g>
    <g class="motion pointer" style="transform:translate(275px,119px)">
      <circle r="30" fill="{CYAN}" opacity=".07"/>
      <g class="motion arrow-skin"><path d="{ARROW}" fill="url(#pointer)" stroke="#E4FAFF" stroke-width="2" stroke-linejoin="round"/></g>
      <g class="motion star-skin" opacity="0" transform="translate(10 13)"><path d="{STAR}" fill="#FDD36D" stroke="#FFF0BE" stroke-width="2" stroke-linejoin="round"/><path d="M-5-1v3m10-3v3" stroke="#6B3D47" stroke-width="2.5" stroke-linecap="round"/></g>
      <g class="motion cat-skin" opacity="0" transform="translate(10 13)"><path d="M-18-3-17-23-5-13Q0-16 5-13L17-23 18-3Q22 21 0 23-22 21-18-3Z" fill="#F3AADE" stroke="#FFE2F5" stroke-width="2"/><path d="M-8 1v4m16-4v4M-3 12q3 4 6 0" stroke="#492651" stroke-width="3" fill="none" stroke-linecap="round"/></g>
    </g>'''
    css = '''
    .pointer { animation:pointer 9s ease-in-out infinite }
    .trail { animation:trail 4s linear infinite }
    .selection { animation:selection 9s steps(1,end) infinite }
    .arrow-skin { animation:arrow 9s steps(1,end) infinite }
    .star-skin { animation:star 9s steps(1,end) infinite }
    .cat-skin { animation:cat 9s steps(1,end) infinite }
    @keyframes pointer { 0%,100% {transform:translate(275px,119px)} 25% {transform:translate(356px,158px)} 50% {transform:translate(321px,211px)} 75% {transform:translate(210px,169px)} }
    @keyframes trail { to {stroke-dashoffset:-214} }
    @keyframes selection { 0%,100% {transform:translateY(0);stroke:#55DDF5} 33% {transform:translateY(51px);stroke:#FDD36D} 66% {transform:translateY(102px);stroke:#F3AADE} }
    @keyframes arrow { 0%,100% {opacity:1} 33%,99% {opacity:0} }
    @keyframes star { 0%,66%,100% {opacity:0} 33% {opacity:1} }
    @keyframes cat { 0%,100% {opacity:0} 66%,99% {opacity:1} }
    '''
    defs = '''<linearGradient id="trail"><stop stop-color="#55DDF5" stop-opacity="0"/><stop offset=".55" stop-color="#55DDF5"/><stop offset="1" stop-color="#D58FFF"/></linearGradient>
    <linearGradient id="pointer" x2="1" y2="1"><stop stop-color="#70EDFA"/><stop offset="1" stop-color="#7766EE"/></linearGradient>'''
    return card("cursor.style", "A little personality in every click.",
                "A pointer moves across a dotted canvas and changes between an arrow, a star and a cat cursor.",
                CYAN, "Pick a cursor", body, css, defs, static=static)


def youtube_card(static=False):
    T.reset()
    swatches = ""
    for x, color in ((385, PURPLE), (408, "#FF7E9F"), (431, CYAN)):
        swatches += f'<circle cx="{x}" cy="222" r="6" fill="{color}"/>'
    body = f'''<defs><linearGradient id="video" x2="1" y2="1"><stop stop-color="#202C51"/><stop offset="1" stop-color="#131A30"/></linearGradient></defs>
    <rect x="24" y="77" width="432" height="170" fill="url(#dots)"/>
    <rect x="39" y="91" width="318" height="141" rx="9" fill="url(#video)" stroke="#314265"/>
    <circle cx="273" cy="124" r="23" fill="#9ABCEB" opacity=".18"/>
    <g class="motion horizon"><path d="M39 181 100 123 162 177 225 138 295 183 357 160V210H39Z" fill="#475A87"/><path d="M39 198 122 160 211 195 289 155 357 191V211H39Z" fill="#687CA5"/><path d="m97 126 21 19-18-5-17 3Z" fill="#C6DDF4" opacity=".75"/></g>
    <rect x="39" y="188" width="318" height="44" rx="9" fill="#090D21"/>
    <rect class="motion skin-bg" x="39" y="188" width="318" height="44" rx="9" fill="#8C5BDF" opacity=".23"/>
    <rect x="52" y="196" width="288" height="3" rx="1.5" fill="#49536D"/>
    <rect class="motion progress skin-fill" x="52" y="195" width="158" height="5" rx="2.5" fill="{PURPLE}"/>
    <circle class="motion knob skin-fill" cx="210" cy="197.5" r="5" fill="{PURPLE}"/>
    <path class="motion skin-fill" d="M54 208V222L66 215ZM76 208V222L86 215ZM87 208H90V222H87ZM100 212H105L111 207V223L105 218H100Z" fill="{PURPLE}"/>
    <path d="M116 211q6 4 0 8m4-12q10 8 0 16M325 208h-5v5m11-5h5v5m0 5v5h-5m-6 0h-5v-5" fill="none" stroke="#D4DEF6" stroke-width="1.5"/>
    {label("01:28 / 04:32", 139, 219, 9, "#CCD9F2", "mono")}
    <rect class="motion skin-frame" x="39" y="91" width="318" height="141" rx="9" fill="none" stroke="{PURPLE}" stroke-width="2"/>
    <g transform="translate(382 103)"><rect width="53" height="27" rx="5" fill="#291D4B" stroke="{PURPLE}"/><path d="m6 19h40M7 7v7l6-3.5Z" stroke="{PURPLE}" fill="{PURPLE}"/><rect y="36" width="53" height="27" rx="5" fill="#432132" stroke="#FF7E9F"/><path d="m6 55h40M7 43v7l6-3.5Z" stroke="#FF7E9F" fill="#FF7E9F"/><rect y="72" width="53" height="27" rx="5" fill="#133D48" stroke="{CYAN}"/><path d="m6 91h40M7 79v7l6-3.5Z" stroke="{CYAN}" fill="{CYAN}"/></g>
    {swatches}'''
    css = '''
    .skin-fill {animation:skin-fill 9s ease-in-out infinite}
    .skin-frame {animation:skin-stroke 9s ease-in-out infinite}
    .skin-bg {animation:skin-fill 9s ease-in-out infinite}
    .progress {animation:progress 9s ease-in-out infinite,skin-fill 9s ease-in-out infinite}
    .knob {animation:knob 9s ease-in-out infinite,skin-fill 9s ease-in-out infinite}
    .horizon {animation:pan 9s ease-in-out infinite}
    @keyframes skin-fill {0%,25%,100% {fill:#AB8AFF} 33%,58% {fill:#FF7E9F} 66%,91% {fill:#55DDF5}}
    @keyframes skin-stroke {0%,25%,100% {stroke:#AB8AFF} 33%,58% {stroke:#FF7E9F} 66%,91% {stroke:#55DDF5}}
    @keyframes progress {0%,100% {width:158px} 85% {width:244px}}
    @keyframes knob {0%,100% {transform:translateX(0)} 85% {transform:translateX(86px)}}
    @keyframes pan {0%,100% {transform:translateX(0)} 50% {transform:translateX(-9px)}}
    '''
    return card("YouTube Skins", "Same video. Your kind of player.",
                "An illustrated video player cycles through purple, pink and cyan controls while its progress bar moves.",
                PURPLE, "Find your skin", body, css, static=static)


def snake_position(t):
    theta = t * math.tau
    return 239 + 131 * math.cos(theta), 161 + 48 * math.sin(theta) + 10 * math.sin(2 * theta)


def slither_card(static=False):
    T.reset()
    foods = ""
    palette = ("#F9B85A", "#C094F3", "#71DBF2", "#EB91C4")
    for i in range(42):
        x, y = 41 + (i * 83 % 398), 96 + (i * 47 % 136)
        color = palette[i % 4]
        foods += f'<circle cx="{x}" cy="{y}" r="4.5" fill="{color}" opacity=".11"/><circle cx="{x}" cy="{y}" r="1.9" fill="{color}" opacity=".85"/>'
    snake = ""
    for i in range(27, -1, -1):
        phase = .23 - i * .01
        x, y = snake_position(phase)
        r = 9 if i == 0 else min(8.1, 3.5 + (27 - i) * .45)
        snake += f'<g class="motion segment" style="transform:translate({x:.2f}px,{y:.2f}px);animation-delay:{-phase*11:.2f}s"><circle cy="3" r="{r+2}" fill="#000" opacity=".27"/><circle r="{r}" fill="url(#snake)" stroke="#98F7FF" stroke-opacity=".28" stroke-width=".8"/>'
        if i == 0:
            # The actual game is made of neon spheres, with no cartoon eye UI.
            snake += '<circle cx="-2" cy="-3" r="3" fill="#E9FDFF" opacity=".6"/>'
        snake += '</g>'
    body = f'''<rect x="24" y="77" width="432" height="170" fill="#060D1B"/>
    <rect x="24" y="77" width="432" height="170" fill="url(#arena)"/>
    {foods}
    <path d="M386 113c-38 8-63-30-92-15" fill="none" stroke="#B686F3" stroke-width="9" stroke-linecap="round" opacity=".55"/>
    <path d="M386 113c-38 8-63-30-92-15" fill="none" stroke="#D9B8FF" stroke-width="4" stroke-linecap="round" opacity=".5"/>
    {snake}
    <rect x="37" y="89" width="99" height="22" rx="11" fill="#11283C" stroke="#285363"/>
    {label("MULTIPLAYER", 86.5, 104, 10, "#A5EAEE", "mono", "middle")}
    <g transform="translate(418 210)" stroke="#608BA8" fill="none" opacity=".7"><circle r="16"/><path d="M-11 0h22M0-11v22" stroke-width=".6"/><circle cx="4" cy="-5" r="2" fill="#89E7F3" stroke="none"/></g>'''
    frames = []
    for i in range(49):
        x, y = snake_position(i / 48)
        frames.append(f'{i/48*100:.3f}%{{transform:translate({x:.2f}px,{y:.2f}px)}}')
    css = '.segment {animation:slither 11s linear infinite}\n@keyframes slither {' + "".join(frames) + '}'
    defs = '''<pattern id="arena" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#244D7C" stroke-width=".6" opacity=".55"/></pattern>
    <radialGradient id="snake" cx=".35" cy=".25"><stop stop-color="#BEFDFF"/><stop offset=".35" stop-color="#53DEF3"/><stop offset="1" stop-color="#158BAB"/></radialGradient>'''
    return card("Slither", "One more orb. One more round.",
                "A cyan snake made of glowing spheres loops around an arena of colored orbs, with a second purple snake nearby.",
                CYAN, "Play a round", body, css, defs, static=static)


def tree(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})"><ellipse cy="3" rx="10" ry="4" fill="#0A2630" opacity=".35"/><path d="M-2-3v7h4v-7" fill="#8C7658"/><path d="M0-33-13-9H13Z" fill="#3EAD86"/><path d="M0-33v24H13Z" fill="#247A72"/><path d="M0-24-16-2H16Z" fill="#4ABF91"/><path d="M0-24V-2H16Z" fill="#288B78"/></g>'''


def house(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})"><path d="m-22 3 28 12 27-17-29-12Z" fill="#183D3A" opacity=".5"/><path d="M-19-23 4-12V9L-19-2Z" fill="#D9D4AE"/><path d="M4-12 27-24V-3L4 9Z" fill="#A8B89E"/><path d="M-24-23-7-41 14-31 4-9Z" fill="#626E81"/><path d="m-7-41 24 9 15 9-18-8Z" fill="#7E8997"/><path d="m14-31-10 22 28-14Z" fill="#475972"/><path d="M-15-19-8-15V-8L-15-12ZM11-10 18-14V-7L11-3Z" fill="#3C7784"/><path d="M-4-12 1-10V7L-4 4Z" fill="#6B6757"/><path d="M-19-8 4 3 27-10M-18-22-18-2M4-12V9M26-22V-3" fill="none" stroke="#7C7561" stroke-width="1.8"/></g>'''


def terra_card(static=False):
    T.reset()
    plants = "".join(tree(x, y, scale) for x, y, scale in [
        (91, 177, .85), (127, 190, .65), (148, 154, .7),
        (334, 178, .7), (358, 185, .9), (372, 199, .75),
        (170, 222, .8), (192, 228, .62), (405, 166, .55)])
    homes = house(239, 174, .72) + house(295, 204, .8) + house(223, 218, .65)
    body = f'''<rect x="24" y="77" width="432" height="170" fill="url(#sky)"/>
    <circle cx="382" cy="108" r="16" fill="#C3F2E5" opacity=".6"/>
    <g class="motion clouds" fill="#CBEBEF" opacity=".27"><path d="M63 110h69l-12-9h-18l-7-8H78Z"/><path d="M305 96h39l-8-8h-22Z"/></g>
    <g class="motion world">
      <path d="M0 145 51 137 92 101 152 139 183 110 226 142 278 113 324 135 370 115 436 145 485 139V300H0Z" fill="#315C65"/>
      <path d="m51 137 41-36 20 24 40 14-61-6ZM152 139l31-29 19 22 24 10-43-6ZM278 113l46 22 46-20-19 31Z" fill="#447879"/>
      <path d="M0 161 76 143 145 162 202 141 265 156 340 144 422 153 485 141V300H0Z" fill="#347C75"/>
      <path d="M0 203 69 165 169 166 209 146 272 164 323 162 375 179 427 166 485 187V300H0Z" fill="#438F77"/>
      <path d="m-6 251 127-71 59 16 84 69Z" fill="#5AA982"/><path d="m323 162 52 17 77 77-184 15Z" fill="#519E7B"/>
      <path d="M174 157q38 15 16 34t59 38 37 37l-36 11q51-15-34-36t-55-53 7-31Z" fill="#4BB7C6"/>
      <path d="M176 162q29 12 8 30t57 41" fill="none" stroke="#91E0D9" stroke-width="1.2" opacity=".6"/>
      <path d="m202 172 49 11 45 33 41 16" fill="none" stroke="#B6B391" stroke-width="7"/>
      <path d="m183 204 38 12 36-22" fill="none" stroke="#B6B391" stroke-width="6"/>
      <path d="m164 194 31 9" stroke="#9C825F" stroke-width="10"/><path d="m164 191 32 9m-33-3 31 9" stroke="#DEC39A" stroke-width="1.8"/>
      {plants}{homes}
      <path d="m75 216 24-13 28 6-25 16Z" fill="#87AF82" opacity=".6"/>
    </g>
    <rect x="37" y="89" width="82" height="22" rx="11" fill="#0B2633" fill-opacity=".8" stroke="#6EA39F" stroke-opacity=".45"/>
    {label("3D WORLD", 78, 104, 10, "#C0EADF", "mono", "middle")}
    <g transform="translate(427 221)" fill="none" stroke="#E1F1DD" opacity=".7"><circle r="12"/><path d="m0-8 4 13-4-2-4 2Z" fill="#E1F1DD" stroke="none"/></g>'''
    css = '''
    .world {transform-origin:240px 175px;animation:flyover 14s ease-in-out infinite}
    .clouds {animation:clouds 14s ease-in-out infinite}
    @keyframes flyover {0%,100% {transform:translate(0,0) scale(1)} 50% {transform:translate(-9px,3px) scale(1.075)}}
    @keyframes clouds {0%,100% {transform:translateX(0)} 50% {transform:translateX(12px)}}
    '''
    defs = '<linearGradient id="sky" x2="0" y2="1"><stop stop-color="#21435F"/><stop offset="1" stop-color="#7CACAF"/></linearGradient>'
    return card("Terra", "A small window into a bigger world.",
                "A slow illustrated flyover of a low-poly valley with cottages, trees, a bridge and a river.",
                "#8AE1BB", "Explore Terra", body, css, defs, static=static)


def main():
    for name, build in (("cursor", cursor_card), ("youtube", youtube_card),
                        ("slither", slither_card), ("terra", terra_card)):
        for static in (False, True):
            # <picture> can select these before loading the image, including
            # browsers that do not pass reduced-motion into external SVG CSS.
            suffix = "-static" if static else ""
            target = ROOT / "assets" / f"product-{name}{suffix}.svg"
            target.write_text(build(static=static), encoding="utf-8")
            print(f"{target.relative_to(ROOT)} - {target.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
