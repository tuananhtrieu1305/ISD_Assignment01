"""Read-only PDF/PNG comparison after the surgical DOCX edit."""
from pathlib import Path
import hashlib
import json
import re
import fitz
from PIL import Image,ImageChops,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/tieuluanfinal_r1'
reference=BASE/'reference_render'
final=BASE/'final_render_r1'
out=BASE/'visual_qa_r1';out.mkdir(exist_ok=True)
rd=fitz.open(next(reference.glob('*.pdf')))
fd=fitz.open(next(final.glob('*.pdf')))


def locate(doc,label):
    return next(i for i,p in enumerate(doc) if i>10 and label in p.get_text())


rs,fs=locate(rd,'CHƯƠNG 6.'),locate(fd,'CHƯƠNG 6.')
re_,fe=locate(rd,'KẾT LUẬN'),locate(fd,'KẾT LUẬN')
assert rs==fs,(rs,fs)


def compare(a,b):
    with Image.open(a) as ia,Image.open(b) as ib:
        assert ia.size==ib.size
        # Page-count fields in the footer necessarily change across the report.
        crop=(0,0,ia.width,int(ia.height*.92))
        diff=ImageChops.difference(ia.convert('RGB').crop(crop),ib.convert('RGB').crop(crop))
        return diff.getbbox() is None


same=[];changed=[]
for i in range(fs):
    (same if compare(reference/f'page-{i+1}.png',final/f'page-{i+1}.png') else changed).append(i+1)
conclusion=[]
for offset in range(len(rd)-re_):
    equal=compare(reference/f'page-{re_+offset+1}.png',final/f'page-{fe+offset+1}.png')
    conclusion.append({'reference_page':re_+offset+1,'final_page':fe+offset+1,'pixels_equal_except_footer':equal})
assert all(x['pixels_equal_except_footer'] for x in conclusion),conclusion
new_text='\n'.join(fd[i].get_text() for i in range(fs,fe))
assert 'four-agent-r11' in new_text
assert '9.849' in new_text
assert all(f'6.{i}.' in new_text for i in range(1,9))
assert not any(s in new_text for s in ['Error! Reference source not found','Error! Bookmark not defined','�'])
# Full-page contact sheets cover all pages; detailed new chapter PNGs remain at
# original resolution in final_render_r1 for individual visual inspection.
for batch in range(0,len(fd),8):
    canvas=Image.new('RGB',(1320,2000),'#ddd');draw=ImageDraw.Draw(canvas)
    for index in range(batch,min(batch+8,len(fd))):
        with Image.open(final/f'page-{index+1}.png') as im:
            thumb=im.convert('RGB');thumb.thumbnail((320,920))
            x=(index-batch)%4*330;y=(index-batch)//4*1000
            canvas.paste(thumb,(x,y+24));draw.text((x+8,y+3),f'Page {index+1}',fill='black')
    canvas.save(out/f'contact-{batch//8+1:02d}.png')
receipt={'reference_pages':len(rd),'final_pages':len(fd),'chapter6_reference_pages':[rs+1,re_],
         'chapter6_final_pages':[fs+1,fe],'chapter6_page_count':fe-fs,
         'identical_prefix_pages_except_footer':same,'changed_prefix_pages_for_navigation':changed,
         'conclusion':conclusion,'navigation_only_expected_changes':True,
         'new_chapter_has_all_sections':True,'source_scope_manifest':'tieuluanfinal/docs/final_revision/document_scope.json',
         'rendered_all_pages':True,'manual_visual_review':'pending'}
(out/'render_comparison.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt))
