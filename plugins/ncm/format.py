import re
import math
from nonebot.adapters.onebot.v11.helpers import MessageSegment as Seg, Message

class Formatter:
    class SearchResult:
        def format(response: dict, offset: int) -> Message:
            songs = response['songs']
            total = response['songCount']

            res = [
                Message([Seg.text(f'Page {offset // 10 + 1} of {math.ceil(total / 10)}')])
            ]
            for i in range(len(songs)):
                res.append(Message([
                    Seg.text(f'#{i}:\n'),
                    Seg.image(songs[i]['al']['picUrl'] + '?param=130y130'),
                    Seg.text(f'\n'),
                    Seg.text(f'{", ".join([ x["name"] for x in songs[i]["ar"] ])} - {songs[i]["name"]}\n'),
                    Seg.text('<unknown album>' if not songs[i]['al'] else f"《{songs[i]['al']['name']}》")
                ]))
            return res
        
    class Detail:
        def format(response: dict) -> Message:
            res = []
            template = Message.template("""{image}
Name: {name}
NCM ID: {id}
Artists: {artists}
Album: {album}
Cover URL: {cover_url}
Requires VIP: {fee}
Quality details:
    Lossless: {quality_lossless}
    High: {quality_high}
    Medium: {quality_med}
    Low: {quality_low}""")
            
            for i in response['songs']:
                if i['fee'] == 0:
                    fee = 'Free'
                elif i['fee'] == 1:
                    fee = 'VIP only'
                elif i['fee'] == 4:
                    fee = 'Album purchase required'
                elif i['fee'] == 8:
                    fee = 'Low quality available for free'
                res.append(template.format_map({
                    'image': Seg.image(i['al']['picUrl']),
                    'name': i['name'],
                    'id': i['id'],
                    'artists': '/'.join([ x['name'] for x in i['ar'] ]),
                    'album': i['al']['name'] if i['al']['name'] else '<unknown album>',
                    'cover_url': i['al']['picUrl'],
                    'fee': fee,
                    'quality_lossless': f"{i['sq']['br'] // 1024} Kbps@{i['sq']['sr'] / 1000} kHz" if i['sq'] else 'N/A',
                    'quality_high': f"{i['h']['br'] // 1024} Kbps@{i['h']['sr'] / 1000} kHz" if i['h'] else 'N/A',
                    'quality_med': f"{i['m']['br'] // 1024} Kbps@{i['m']['sr'] / 1000} kHz" if i['m'] else 'N/A',
                    'quality_low': f"{i['l']['br'] // 1024} Kbps@{i['l']['sr'] / 1000} kHz" if i['l'] else 'N/A'
                }))

            return res

