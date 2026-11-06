from pathlib import Path
import base64, json
p=Path(__file__).parent
h=(p/'viewer_template.html').read_text()
h=h.replace('__MODEL_BASE64__',(p/'model_payload.b64').read_text())
tx={name:base64.b64encode((p/name).read_bytes()).decode() for name in ['lcars.png','side_screen.png','stars.png']}
h=h.replace('__TEXTURES_JSON__',json.dumps(tx,separators=(',',':')))
previews={name:base64.b64encode((p/f'preview_{name}.jpg').read_bytes()).decode() for name in ['overview','captain','helm','tactical','wall']}
h=h.replace('__PREVIEW_JSON__',json.dumps(previews,separators=(',',':')))
(p/'Open_Bridge_Walkthrough.html').write_text(h)
print('Viewer bytes',len(h),'textures',[(k,len(v)) for k,v in tx.items()])
