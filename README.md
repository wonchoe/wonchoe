<div align="center">
  <img src="assets/hero.svg" width="100%" alt="Oleksii Semeniuk - playful products up front, edge, cluster and pipelines behind">
</div>

<div align="center">

[![cursor.style](https://img.shields.io/badge/cursor.style-live-38BDF8?style=flat-square&labelColor=0B1130&logo=googlechrome&logoColor=white)](https://cursor.style) [![LinkedIn](https://img.shields.io/badge/LinkedIn-oleksisem-6366F1?style=flat-square&labelColor=0B1130&logo=linkedin&logoColor=white)](https://linkedin.com/in/oleksisem/) [![Telegram](https://img.shields.io/badge/Telegram-wonchoe-A855F7?style=flat-square&labelColor=0B1130&logo=telegram&logoColor=white)](https://t.me/wonchoe) [![Followers](https://img.shields.io/github/followers/wonchoe?style=flat-square&labelColor=0B1130&color=EC4899&logo=github&logoColor=white&label=followers)](https://github.com/wonchoe) ![Profile views](https://komarev.com/ghpvc/?username=wonchoe&label=views&color=0B1130&style=flat-square) [![Traffic sync](https://img.shields.io/github/actions/workflow/status/wonchoe/wonchoe/main.yml?style=flat-square&labelColor=0B1130&color=FFC23C&label=daily%20refresh)](https://github.com/wonchoe/wonchoe/actions/workflows/main.yml)

</div>

## What I do

I build browser products for people who are mostly not developers - a kid picking a rainbow cursor, a teenager reskinning their YouTube player - and I run everything underneath them myself: Cloudflare at the edge, k3s and Argo CD in the middle, MySQL, MongoDB and object storage at the back.

So the interesting problems are rarely the pretty ones. Judging every photo and message in the room before anyone else sees it. Keeping one container image from eating a node. Serving nine figures of requests a month on a budget that would make a funded startup laugh.

## What I run

| Product | What it is | Reach |
| :-- | :-- | :-- |
| **[cursor.style](https://cursor.style)** | The largest free cursor library, plus the extension that applies them | [![users](https://img.shields.io/chrome-web-store/users/bmjmipppabdlpjccanalncobmbacckjn?style=flat-square&label=users&color=6366F1&labelColor=0B1130)](https://chromewebstore.google.com/detail/bmjmipppabdlpjccanalncobmbacckjn) [![rating](https://img.shields.io/chrome-web-store/rating/bmjmipppabdlpjccanalncobmbacckjn?style=flat-square&label=rating&color=FFC23C&labelColor=0B1130)](https://chromewebstore.google.com/detail/bmjmipppabdlpjccanalncobmbacckjn) |
| **[cursor-land.com](https://cursor-land.com)** | Second cursor brand - same engine, its own audience | [![users](https://img.shields.io/chrome-web-store/users/oinkhgpjmeccknjbbccabjfonamfmcbn?style=flat-square&label=users&color=6366F1&labelColor=0B1130)](https://chromewebstore.google.com/detail/oinkhgpjmeccknjbbccabjfonamfmcbn) [![rating](https://img.shields.io/chrome-web-store/rating/oinkhgpjmeccknjbbccabjfonamfmcbn?style=flat-square&label=rating&color=FFC23C&labelColor=0B1130)](https://chromewebstore.google.com/detail/oinkhgpjmeccknjbbccabjfonamfmcbn) |
| **[youtube-skins.com](https://youtube-skins.com)** | 130+ skins for the YouTube player, and an ad skipper beside it | [![users](https://img.shields.io/chrome-web-store/users/imomahaddnhnhfggpmpbphdiobpmahof?style=flat-square&label=users&color=6366F1&labelColor=0B1130)](https://chromewebstore.google.com/detail/imomahaddnhnhfggpmpbphdiobpmahof) [![rating](https://img.shields.io/chrome-web-store/rating/imomahaddnhnhfggpmpbphdiobpmahof?style=flat-square&label=rating&color=FFC23C&labelColor=0B1130)](https://chromewebstore.google.com/detail/imomahaddnhnhfggpmpbphdiobpmahof) |
| **[fb.zone](https://fb.zone)** | Video and photo background themes for Facebook | [![users](https://img.shields.io/chrome-web-store/users/oodajhdbojacdmkhkiafdhicifcdjoig?style=flat-square&label=users&color=6366F1&labelColor=0B1130)](https://chromewebstore.google.com/detail/oodajhdbojacdmkhkiafdhicifcdjoig) [![rating](https://img.shields.io/chrome-web-store/rating/oodajhdbojacdmkhkiafdhicifcdjoig?style=flat-square&label=rating&color=FFC23C&labelColor=0B1130)](https://chromewebstore.google.com/detail/oodajhdbojacdmkhkiafdhicifcdjoig) |
| **[Chat](https://cursor.style)** | Moderated rooms, direct messages, photo albums and WebRTC calls, built into the main site | rooms, DMs, group voice |
| **[Slither](https://cursor.style/games/slither)** | Free multiplayer snake, no install, no account | live on the games hub |
| **[Terra](https://terra.cursor.style)** | Open 3D world you can run around in, built on streamed low-poly terrain | in preview |
| **[agropost.com.ua](https://agropost.com.ua)** | Ukrainian agricultural marketplace: listings, company catalogue, grain logistics | running since 2010 |
| **[agro-post.com](https://agro-post.com)** | The same platform for the US market | live |

<sub>Counts and ratings are pulled live from the Chrome Web Store every time this page loads.</sub>

## The one that got big

<div align="center">
  <img src="logo.png" width="300" alt="cursor.style v5">
</div>

<div align="center">
  <img src="assets/traffic.svg" width="100%" alt="cursor.style traffic over the last 30 days">
</div>

<!-- CF-STATS:START -->

**148,421,034** requests &nbsp;·&nbsp; **16,953,289** page views &nbsp;·&nbsp; **5,219,280** unique visitors &nbsp; over the last 30 days

<sub>Yesterday alone: 5,313,755 requests from 200,855 people. Refreshed 2026-09-11 by the workflow above.</sub>

<!-- CF-STATS:END -->

## The one with the moderation problem

The chat grew out of the cursor library and runs in the same pod as the site: rooms, direct messages, photo albums, group voice and WebRTC calls, in 49 languages. Most of the people in it are teenagers, and that one fact decides almost everything about how it has to be built.

So the hard part was never the sockets. It is that every username, every message and every photo has to be judged before anyone else sees it, in languages I do not read, in under a second, at a cost per item of approximately nothing.

| Layer | What runs |
| :-- | :-- |
| **Photos** | OpenAI `omni-moderation-latest`, with per-category score thresholds measured against real uploads rather than guessed |
| **A second opinion on photos** | Amazon Rekognition, wired in beside it and running in shadow: it logs its labels and decides nothing until they prove the thresholds. The two miss different things - a real shotgun scored 0 at OpenAI and 100 at Rekognition, which is the whole argument for keeping both |
| **Text** | The same moderation model, then `gpt-4o-mini` on what scores zero and is still a problem: a phone number handed over in a direct message, or an intent that only reads as harmful in the language it was written in |
| **Words** | A two-level dictionary per language, because in some of them a slur is one space away from an ordinary phrase, and a naive filter bans half the room |
| **Reports** | Triaged automatically before a human opens them, with a ladder of sanctions that does not wait for one |
| **Warnings** | Treated as a product rather than a log line: a badge beside the avatar, a modal the account has to acknowledge, and a record of what was decided and when |

Failing open is the expensive direction here, so an outage at the moderator fails the upload instead of waving it through.

<div align="center">
  <img src="assets/chat.svg" width="100%" alt="The cursor.style chat in numbers">
</div>

## The one universities cite

AgroPost has run since 2010: a marketplace, company catalogue and grain-logistics board for Ukrainian agriculture, now with a US edition at [agro-post.com](https://agro-post.com). It is the least glamorous thing I operate and the one that ended up in other people's teaching materials.

| Institution | Where it appears | Year |
| :-- | :-- | :-- |
| Odesa State Agrarian University | [Course work programme](https://osau.edu.ua/wp-content/uploads/2026/03/OP-02_RP_TVPR-H7-2025-26.pdf), listing AgroPost as a notice board, company catalogue and trading platform | 2025 |
| Mykolaiv National Agrarian University | [Methodical recommendations](https://www.mnau.edu.ua/files/faculty/agronomij/opp/tehnologiya-virobnictva-produkciyi-roslinnictva-metodichni-rekomendaciyi.pdf) for crop production technology | 2021 |
| Mykolaiv National Agrarian University | [Technical crops](https://dspace.mnau.edu.ua/jspui/bitstream/123456789/2387/1/Tekhnichni_kultury.pdf) teaching material | 2016 |
| National University of Food Technologies | [Conference proceedings](https://conference.nuft.edu.ua/leanfoodpack/Books/Abstracts/A_2015.pdf), bibliography citing the elevators directory | 2015 |

## How it holds together

<div align="center">
  <img src="assets/architecture.svg" width="100%" alt="Browsers and extensions reach Cloudflare, which fronts a k3s cluster running Laravel, Node and workers over MySQL, MongoDB, Redis, Meilisearch and R2; GitHub Actions and Argo CD deliver it, AWS SSM and External Secrets configure it, Grafana watches it">
</div>

Five public brands, one cluster, one operator. Nothing reaches production except through Git: Actions builds and pushes the image, Argo CD syncs the manifests, External Secrets pulls configuration out of AWS Parameter Store, and Cloudflare Zero Trust is the only door into the admin side. If it is not in a repository, it is not running.

## Certifications

<div align="center">
<table>
  <tr>
    <td align="center" width="25%"><img src="assets/devops-pro.png" width="96" alt=""><br><sub><b>AWS DevOps Engineer</b><br>Professional</sub></td>
    <td align="center" width="25%"><img src="assets/solut-assoc.png" width="96" alt=""><br><sub><b>AWS Solutions Architect</b><br>Associate</sub></td>
    <td align="center" width="25%"><img src="assets/aws-pract.png" width="96" alt=""><br><sub><b>AWS Cloud Practitioner</b><br>Foundational</sub></td>
    <td align="center" width="25%"><img src="assets/koob.png" width="96" alt=""><br><sub><b>Kubernetes &amp; Cloud Native</b><br>Associate (KCNA)</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="assets/gitops-ent.png" width="96" alt=""><br><sub><b>GitOps Certified</b><br>Enterprise · Codefresh</sub></td>
    <td align="center"><img src="assets/gitops-fund.png" width="96" alt=""><br><sub><b>GitOps Certified</b><br>Fundamentals · Codefresh</sub></td>
    <td align="center"><img src="assets/image.png" width="96" alt=""><br><sub><b>GitHub Actions</b><br>Certification Program</sub></td>
    <td align="center"><img src="assets/mta.png" width="96" alt=""><br><sub><b>Microsoft MTA</b><br>Networking Fundamentals</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="assets/badge-claude-bedrock.svg" width="96" alt=""><br><sub><b>Claude with Amazon Bedrock</b><br>Anthropic · September 2026</sub></td>
    <td align="center"><img src="assets/badge-copilot.svg" width="96" alt=""><br><sub><b>GitHub Copilot</b><br>Core Skills · March 2026</sub></td>
    <td align="center"><img src="assets/badge-gh-migrations.svg" width="96" alt=""><br><sub><b>Azure DevOps to GitHub</b><br>Enterprise migrations · December 2025</sub></td>
    <td></td>
  </tr>
</table>
</div>

<sub>Eleven in total. The last three are set in this page's own style, because the issuers publish no badge artwork for them.</sub>

## Toolbox

**Edge and delivery**
![Cloudflare](https://img.shields.io/badge/Cloudflare-0B1130?style=flat-square&logo=cloudflare&logoColor=F38020) ![AWS](https://img.shields.io/badge/AWS-0B1130?style=flat-square&logo=amazonwebservices&logoColor=FF9900) ![Kubernetes](https://img.shields.io/badge/k3s-0B1130?style=flat-square&logo=kubernetes&logoColor=326CE5) ![Argo CD](https://img.shields.io/badge/Argo%20CD-0B1130?style=flat-square&logo=argo&logoColor=EF7B4D) ![Docker](https://img.shields.io/badge/Docker-0B1130?style=flat-square&logo=docker&logoColor=2496ED) ![Terraform](https://img.shields.io/badge/Terraform-0B1130?style=flat-square&logo=terraform&logoColor=7B42BC) ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-0B1130?style=flat-square&logo=githubactions&logoColor=2088FF)

**Services and data**
![PHP](https://img.shields.io/badge/PHP-0B1130?style=flat-square&logo=php&logoColor=777BB4) ![Laravel](https://img.shields.io/badge/Laravel-0B1130?style=flat-square&logo=laravel&logoColor=FF2D20) ![Node.js](https://img.shields.io/badge/Node.js-0B1130?style=flat-square&logo=nodedotjs&logoColor=5FA04E) ![MySQL](https://img.shields.io/badge/MySQL-0B1130?style=flat-square&logo=mysql&logoColor=4479A1) ![MongoDB](https://img.shields.io/badge/MongoDB-0B1130?style=flat-square&logo=mongodb&logoColor=47A248) ![Redis](https://img.shields.io/badge/Redis-0B1130?style=flat-square&logo=redis&logoColor=FF4438) ![WebRTC](https://img.shields.io/badge/WebRTC-0B1130?style=flat-square&logo=webrtc&logoColor=333333)

**In the browser**
![JavaScript](https://img.shields.io/badge/JavaScript-0B1130?style=flat-square&logo=javascript&logoColor=F7DF1E) ![TypeScript](https://img.shields.io/badge/TypeScript-0B1130?style=flat-square&logo=typescript&logoColor=3178C6) ![Chrome extensions](https://img.shields.io/badge/Chrome%20extensions-0B1130?style=flat-square&logo=googlechrome&logoColor=4285F4) ![Tailwind](https://img.shields.io/badge/Tailwind-0B1130?style=flat-square&logo=tailwindcss&logoColor=06B6D4) ![Three.js](https://img.shields.io/badge/Three.js-0B1130?style=flat-square&logo=threedotjs&logoColor=FFFFFF) ![Python](https://img.shields.io/badge/Python-0B1130?style=flat-square&logo=python&logoColor=3776AB)

## On GitHub

<div align="center">
  <img src="assets/github.svg" width="100%" alt="30 public repositories, 342 contributions in the last twelve months, mostly JavaScript, PHP and HTML">
</div>

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/wonchoe/wonchoe/output/snake-dark.svg">
    <img src="https://raw.githubusercontent.com/wonchoe/wonchoe/output/snake-light.svg" alt="A snake eating this year's contribution squares">
  </picture>
</div>

## Worth a look

| Repository | What it does |
| :-- | :-- |
| **[laravel-gsc-manager](https://github.com/wonchoe/laravel-gsc-manager)** | Google Search Console inside Laravel, authenticated with a service account |
| **[ai-php-json-files-language-translator](https://github.com/wonchoe/ai-php-json-files-language-translator)** | Translates PHP, JSON and plain-text language files with an LLM, keeping placeholders intact |
| **[tabler-icons-font-picker](https://github.com/wonchoe/tabler-icons-font-picker)** | Tabler icon picker with categories, search and a drop-in field |
| **[image-processing](https://github.com/wonchoe/image-processing)** | Image pipeline on AWS: ECS, Lambda, Aurora and S3 |
| **[slither](https://github.com/wonchoe/slither)** | The multiplayer snake running at [cursor.style/games](https://cursor.style/games) |

<details>
<summary><b>How this page builds itself</b></summary>

<br>

Nothing here is a screenshot, and no image is hand-placed pixel art.

- **`assets/hero.svg`** is generated by `tools/build_hero.py`. GitHub serves README images under `default-src 'none'`, so an SVG can never pull a web font down. Every piece of display type is therefore baked into `<path>` outlines from ASCII subsets of Baloo 2 and JetBrains Mono, kept in `tools/fonts/` with their OFL licences. The mascot is embedded as a data URI for the same reason.
- **`assets/traffic.svg`** is redrawn every night. `update_readme.mjs` asks the Cloudflare GraphQL API for yesterday and for the last 30 days, writes `assets/traffic.json`, and `tools/build_traffic.py` turns that into the chart above - bars, busiest-day marker, aligned figures and all.
- **`assets/github.svg`** is the same idea pointed at the GitHub GraphQL API. The usual readme-stats services were answering 503 and 402 while this page was built, so the card is generated here instead and cannot go down on its own.
- **The numbers in the text** come from the same run, so the readable version stays correct even if images are blocked.
- **The snake** is redrawn from the contribution graph by a second workflow and published to the `output` branch.

Rebuild the artwork locally with:

```bash
pip install fonttools pillow
python tools/build_hero.py
python tools/build_traffic.py
GITHUB_TOKEN=... python tools/build_github_card.py
```

</details>

## Say hello

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Oleksii%20Semeniuk-6366F1?style=for-the-badge&labelColor=0B1130&logo=linkedin&logoColor=white)](https://linkedin.com/in/oleksisem/) [![Telegram](https://img.shields.io/badge/Telegram-@wonchoe-A855F7?style=for-the-badge&labelColor=0B1130&logo=telegram&logoColor=white)](https://t.me/wonchoe) [![cursor.style](https://img.shields.io/badge/cursor.style-the%20cursor%20library-38BDF8?style=for-the-badge&labelColor=0B1130&logo=googlechrome&logoColor=white)](https://cursor.style)

