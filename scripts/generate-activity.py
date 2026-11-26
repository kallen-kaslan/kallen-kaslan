#!/usr/bin/env python3
"""Generate a self-contained animated contribution SVG from GitHub GraphQL data."""
import argparse, datetime as dt, html, json, math, os, pathlib, urllib.request

QUERY = '''query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount } }
      }
    }
  }
}'''

def fetch(login):
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('GITHUB_TOKEN is missing')
    request = urllib.request.Request('https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': login}}).encode(),
        headers={'Authorization': 'Bearer '+token, 'Content-Type':'application/json', 'User-Agent':'Living-Identity-Activity'}, method='POST')
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get('errors'):
        raise RuntimeError('GitHub GraphQL: '+ '; '.join(e.get('message','Unknown error') for e in result['errors']))
    return result['data']['user']['contributionsCollection']['contributionCalendar']

def render(cal, demo=False):
    weeks = cal['weeks']
    if not 1 <= len(weeks) <= 54: raise ValueError('Unexpected calendar length')
    days = [d for w in weeks for d in w['contributionDays']]
    if not days: raise ValueError('No calendar days')
    for d in days:
        dt.date.fromisoformat(d['date'])
        if not 0 <= d['weekday'] <= 6 or not isinstance(d['contributionCount'], int) or d['contributionCount'] < 0: raise ValueError('Invalid day')
    total = int(cal['totalContributions'])
    dates = sorted(d['date'] for d in days)
    weekly = [sum(d['contributionCount'] for d in w['contributionDays']) for w in weeks]
    max_day = max(d['contributionCount'] for d in days)
    max_week = max(weekly)
    active = sum(d['contributionCount'] > 0 for d in days)
    n = len(weeks); x0=91; end=916; step=(end-x0)/(max(n,2)-1); size=min(12.1,step-3); y0=102
    fmt=lambda x:f'{x:.2f}'
    esc=lambda x:html.escape(str(x))
    label='SAMPLE DATA — NOT ACTUAL GITHUB ACTIVITY' if demo else 'GITHUB CONTRIBUTIONS / API DATA'
    title='Illustrative sample activity' if demo else 'GitHub contribution activity'
    colors=['#273044','#42547E','#637BB3','#9A9BDE','#C8BCFF']
    def level(count):
        return 0 if not count else min(4, 1+int(3*math.log(count)/math.log(max(2,max_day))))
    grid=[]; months=[]; last_month=None
    for i,w in enumerate(weeks):
        x=x0+i*step
        for d in w['contributionDays']:
            count=d['contributionCount']; y=y0+d['weekday']*16
            grid.append(f'<rect x="{fmt(x)}" y="{y}" width="{fmt(size)}" height="12" rx="2.5" fill="{colors[level(count)]}"/>')
        if w['contributionDays']:
            date=dt.date.fromisoformat(w['contributionDays'][0]['date']); month=(date.year,date.month)
            if month!=last_month and i < n-1:
                months.append(f'<text x="{fmt(x)}" y="92">{date.strftime("%b")}</text>');last_month=month
    points=[(x0+i*step+size/2, 277-(v/max(1,max_week))*48) for i,v in enumerate(weekly)]
    if len(points)==1: points.append((end,points[0][1]))
    path='M'+' L'.join(f'{fmt(x)} {fmt(y)}' for x,y in points)
    area=path+f' L{fmt(points[-1][0])} 278 L{fmt(points[0][0])} 278 Z'
    date_text=f'{dates[0]} — {dates[-1]}'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="326" viewBox="0 0 960 326" role="img" aria-labelledby="title desc">
<title id="title">{esc(title)}</title><desc id="desc">{esc(label)}. {total} contributions, {active} active days. {esc(date_text)}. Calendar and weekly totals.</desc>
<defs>
 <linearGradient id="base" x2="1" y2="1"><stop stop-color="#12192B"/><stop offset="1" stop-color="#25263F"/></linearGradient>
 <radialGradient id="ambient"><stop stop-color="#6E7ED2" stop-opacity=".43"/><stop offset="1" stop-color="#6E7ED2" stop-opacity="0"/></radialGradient>
 <radialGradient id="ambient2"><stop stop-color="#9C79C9" stop-opacity=".30"/><stop offset="1" stop-color="#9C79C9" stop-opacity="0"/></radialGradient>
 <linearGradient id="sweep"><stop stop-color="#B9CEFF" stop-opacity="0"/><stop offset=".73" stop-color="#B9CEFF" stop-opacity=".24"/><stop offset=".95" stop-color="#D6E2FF" stop-opacity=".7"/><stop offset="1" stop-color="#B9CEFF" stop-opacity="0"/></linearGradient>
 <linearGradient id="line" x2="1" y2="0"><stop stop-color="#819CFA"/><stop offset="1" stop-color="#C6AEF1"/></linearGradient>
 <linearGradient id="area" x2="0" y2="1"><stop stop-color="#A0A9F1" stop-opacity=".24"/><stop offset="1" stop-color="#A0A9F1" stop-opacity="0"/></linearGradient>
 <clipPath id="panel"><rect x=".5" y=".5" width="959" height="325" rx="12"/></clipPath>
 <clipPath id="cells"><rect x="91" y="102" width="838" height="108"/></clipPath>
 <mask id="tiles" maskUnits="userSpaceOnUse" x="0" y="0" width="960" height="326"><g fill="white">{''.join(r.split(' fill=')[0]+' fill="white"/>' for r in grid)}</g></mask>
</defs>
<style>@media (prefers-reduced-motion: reduce) {{ .motion {{ display:none; }} }}</style>
<g clip-path="url(#panel)">
 <rect width="960" height="326" fill="url(#base)"/>
 <ellipse cx="740" cy="85" rx="420" ry="240" fill="url(#ambient)" opacity=".55"/>
 <g class="motion"><ellipse cx="170" cy="0" rx="400" ry="250" fill="url(#ambient)"><animate attributeName="cx" values="170;810;170" dur="8s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".42 0 .58 1;.42 0 .58 1"/></ellipse><ellipse cx="820" cy="300" rx="440" ry="230" fill="url(#ambient2)"><animate attributeName="cx" values="820;220;820" dur="8s" repeatCount="indefinite"/></ellipse></g>
 <g font-family="Arial, Helvetica, sans-serif">
  <text x="30" y="28" font-size="10" letter-spacing="2.2" fill="#A7B5D4">{esc(label)}</text>
  <text x="30" y="62" font-size="28" font-weight="700" fill="#EEF0FA">{total:,}<tspan font-size="14" font-weight="400" fill="#BFC9E1"> contributions</tspan></text>
  <text x="925" y="35" font-size="12" text-anchor="end" fill="#DCE2F4">{active} active days</text>
  <text x="925" y="56" font-size="10" text-anchor="end" fill="#AAB6D2">{esc(date_text)}</text>
  <path d="M30 72H930" stroke="#8190B6" stroke-opacity=".24"/>
  <g font-size="9.5" fill="#C1CBE3">{''.join(months)}<text x="30" y="127">Mon</text><text x="30" y="159">Wed</text><text x="30" y="191">Fri</text></g>
  {''.join(grid)}
  <g class="motion" mask="url(#tiles)" clip-path="url(#cells)"><rect x="-150" y="101" width="145" height="110" fill="url(#sweep)"><animate attributeName="x" values="-150;950;950" keyTimes="0;.76;1" dur="8s" repeatCount="indefinite"/></rect></g>
  <path d="M30 220H930" stroke="#8190B6" stroke-opacity=".24"/>
  <text x="30" y="236" font-size="9" fill="#C1CBE3">{max(1,max_week)}</text><text x="30" y="279" font-size="9" fill="#C1CBE3">0</text>
  <path d="M91 229H930 M91 254H930 M91 278H930" stroke="#8291BD" stroke-opacity=".18" stroke-dasharray="3 5"/>
  <path d="{area}" fill="url(#area)"/>
  <path d="{path}" fill="none" stroke="url(#line)" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>
  <g class="motion"><g><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.045;.955;1" dur="8s" repeatCount="indefinite"/><circle r="7" fill="#C5CBFF" opacity=".22"><animate attributeName="r" values="5;9;5" dur="1s" repeatCount="indefinite"/></circle><circle r="2.8" fill="#F0EDFF"/><animateMotion path="{path}" dur="8s" repeatCount="indefinite" calcMode="paced"/></g></g>
  <text x="30" y="305" font-size="10" letter-spacing="1.5" fill="#B9C5DF">WEEKLY ACTIVITY SIGNAL</text>
  <text x="768" y="305" font-size="9" fill="#B9C5DF">Less</text>
  {''.join(f'<rect x="{796+i*19}" y="295" width="13" height="12" rx="2" fill="{c}"/>' for i,c in enumerate(colors))}
  <text x="897" y="305" font-size="9" fill="#B9C5DF">More</text>
 </g>
</g><rect x=".5" y=".5" width="959" height="325" rx="12" fill="none" stroke="#637197" stroke-opacity=".55"/>
</svg>'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--login',default=os.environ.get('GITHUB_REPOSITORY_OWNER','kallen-kaslan'));p.add_argument('--output',default='assets/contribution-signal.svg');p.add_argument('--fixture',help='Local sample calendar JSON (labels output as sample)');a=p.parse_args()
    data=json.loads(pathlib.Path(a.fixture).read_text()) if a.fixture else fetch(a.login)
    svg=render(data,demo=bool(a.fixture));target=pathlib.Path(a.output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(svg,encoding='utf-8');print(f'Wrote {target} ({len(svg.encode()):,} bytes)')
if __name__=='__main__': main()
