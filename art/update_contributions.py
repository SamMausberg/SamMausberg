"""Refresh the profile's contribution artwork from GitHub's public calendar.

Uses Python's standard library and no token. A changed/invalid response fails
before touching the previous artwork. Counts and intensity levels come from
GitHub; there are no invented dates or decorative contribution values.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
from urllib.request import Request, urlopen

class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells=[]
        self.tips={}
        self.tip_id=None
        self.in_total=False
        self.total_text=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='td' and 'data-date' in a:self.cells.append(a)
        if tag=='tool-tip':
            self.tip_id=a.get('for')
            self.tips[self.tip_id]=''
        if tag=='h2' and a.get('id')=='js-contribution-activity-description':self.in_total=True
    def handle_data(self,data):
        if self.tip_id:self.tips[self.tip_id]+=data
        if self.in_total:self.total_text+=data
    def handle_endtag(self,tag):
        if tag=='tool-tip':self.tip_id=None
        if tag=='h2':self.in_total=False

def parse_calendar(raw,username):
    p=CalendarParser()
    p.feed(raw.decode('utf-8'))
    days=[]
    for cell in p.cells:
        label=p.tips.get(cell['id'],'').strip()
        m=re.match(r'([\d,]+) contributions? on ',label)
        if m:count=int(m.group(1).replace(',',''))
        elif label.startswith('No contributions on '):count=0
        else:raise ValueError('GitHub count format changed: '+label)
        idx=re.fullmatch(r'contribution-day-component-(\d+)-(\d+)',cell['id'])
        if not idx:raise ValueError('GitHub calendar index format changed')
        dt=date.fromisoformat(cell['data-date'])
        weekday,week=map(int,idx.groups())
        level=int(cell['data-level'])
        if not 0<=level<=4 or weekday!=(dt.weekday()+1)%7:raise ValueError('Invalid level or weekday')
        if count<0 or (count==0)!=(level==0):raise ValueError('Inconsistent count and intensity')
        days.append(dict(date=dt.isoformat(),count=count,level=level,weekday=weekday,week=week))
    days.sort(key=lambda d:d['date'])
    if not 350<=len(days)<=378:raise ValueError('Expected a complete year of calendar days')
    first=date.fromisoformat(days[0]['date'])
    if [d['date'] for d in days]!=[(first+timedelta(days=i)).isoformat() for i in range(len(days))]:
        raise ValueError('Calendar dates are duplicated or discontinuous')
    if any(d['week']!=(date.fromisoformat(d['date'])-first).days//7 for d in days):
        raise ValueError('Calendar week positions do not match dates')
    summary=re.search(r'([\d,]+)\s+contributions?\b',p.total_text)
    total=sum(d['count'] for d in days)
    if not summary or int(summary.group(1).replace(',',''))!=total:
        raise ValueError('Daily sum does not match GitHub headline total')
    return dict(username=username,source=f'https://github.com/users/{username}/contributions',
                fetchedAt=datetime.now(timezone.utc).isoformat(),
                sourceSha256=hashlib.sha256(raw).hexdigest(),
                start=days[0]['date'],end=days[-1]['date'],total=total,days=days)

def render_svg(data):
    esc=html.escape
    palette=['#263f48','#377375','#74a692','#d3af68','#ffe092']
    title=f"{data['total']:,} GitHub contributions · {data['start']} to {data['end']}"
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 235" role="img" aria-labelledby="contrib-title contrib-desc">',
           f'<title id="contrib-title">{esc(title)}</title>',
           '<desc id="contrib-desc">A woven contribution calendar. Columns are weeks, rows run Sunday to Saturday. Each light is one actual day; brighter colors mean higher GitHub contribution intensity.</desc>',
           '<style>text{font-family:system-ui,-apple-system,Segoe UI,sans-serif}g.day:hover rect,g.day:focus rect{stroke:#fff;stroke-width:2.5;outline:none}</style>',
           '<rect width="1600" height="235" rx="4" fill="#101e27"/>',
           f'<text x="44" y="38" fill="#e8dfc9" font-size="22">{data["total"]:,} contributions</text>',
           '<text x="1556" y="38" fill="#8eaaa9" font-size="17" text-anchor="end">ONE LIGHT, ONE DAY</text>']
    max_week=max(d['week'] for d in data['days'])
    def point(week,weekday):
        x=74+week*1452/max_week
        y=92+weekday*10+14*math.sin(week/7.3)+5*math.sin(week/2.9)
        return x,y
    for weekday in range(7):
        coords=[point(w,weekday) for w in range(max_week+1)]
        path='M '+' L '.join(f'{x:.2f} {y:.2f}' for x,y in coords)
        parts.append(f'<path d="{path}" fill="none" stroke="#3b6464" stroke-opacity=".32" stroke-width="1"/>')
    for d in data['days']:
        x,y=point(d['week'],d['weekday'])
        label=f"{d['date']}: {d['count']:,} contribution{'s' if d['count']!=1 else ''}"
        color=palette[d['level']]
        parts.append(f'<g class="day" tabindex="0" role="img" aria-label="{esc(label)}" data-date="{d["date"]}" data-count="{d["count"]}" data-level="{d["level"]}"><title>{esc(label)}</title>')
        if d['level']==4:parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="{color}" opacity=".08"/>')
        parts.append(f'<rect x="{x-3.5:.2f}" y="{y-3.5:.2f}" width="7" height="7" rx="1.5" fill="{color}" transform="rotate(18 {x:.2f} {y:.2f})"/></g>')
    first=date.fromisoformat(data['start']).strftime('%b %d, %Y')
    last=date.fromisoformat(data['end']).strftime('%b %d, %Y')
    parts.append(f'<text x="44" y="213" fill="#8eaaa9" font-size="17">{first} – {last}</text>')
    for i,c in enumerate(palette):parts.append(f'<rect x="{1402+i*26}" y="199" width="15" height="15" rx="3" fill="{c}"/>')
    parts.extend(['<text x="1388" y="213" fill="#8eaaa9" font-size="15" text-anchor="end">Less</text>',
                  '<text x="1538" y="213" fill="#8eaaa9" font-size="15">More</text>','</svg>'])
    return '\n'.join(parts)+'\n'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--username',default='SamMausberg')
    p.add_argument('--source-file',type=Path)
    p.add_argument('--out-root',type=Path,default=Path(__file__).resolve().parents[1])
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}',a.username):raise ValueError('Invalid GitHub username')
    if a.source_file:raw=a.source_file.read_bytes()
    else:
        req=Request(f'https://github.com/users/{a.username}/contributions',headers={'User-Agent':'profile-contribution-art/1.0','Accept':'text/html'})
        with urlopen(req,timeout=40) as r:raw=r.read(5_000_000)
    data=parse_calendar(raw,a.username)
    svg=render_svg(data)
    # Validation above finishes before either existing output is replaced.
    for rel,content in [('assets/contributions.svg',svg),('data/contributions.json',json.dumps(data,indent=2)+'\n')]:
        out=a.out_root/rel
        out.parent.mkdir(parents=True,exist_ok=True)
        temp=out.with_suffix(out.suffix+'.tmp')
        temp.write_text(content,encoding='utf-8',newline='\n')
        temp.replace(out)
    print(f"Verified {len(data['days'])} days; {data['total']:,} contributions match GitHub's headline.")

if __name__=='__main__':main()
