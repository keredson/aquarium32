import os
import re

import uttp
import json


CLASS_MAP = None

def init(jsx_path='static', serve_root='/static'):
  global CLASS_MAP
  CLASS_MAP = {}
  jsx_path = jsx_path.rstrip('/')
  serve_root = serve_root.rstrip('/')
  pattern = re.compile(r'class\s+(\w+)\s+extends\s+React.Component')
  for fn in os.listdir(jsx_path):
    if not fn.endswith('.jsx'): continue
    full_fn = jsx_path +'/'+ fn
    print('found:', full_fn)
    with open(full_fn) as f:
      while line := f.readline():
        m = pattern.search(line)
        if m:
          print('found', m.group(1), 'in', full_fn)
          CLASS_MAP[m.group(1)] = serve_root +'/'+ fn
  print('CLASS_MAP', CLASS_MAP)

#init()



@uttp.get(r'/__uttpreact__')
def __uttpreact__(req):
  yield uttp.header('Content-Type', 'text/javascript')
  yield uttp.header('Cache-Control', 'max-age=%i' % 604800)
  yield '''
    class ___UTTPReact_Stub__ extends React.Component {
      constructor(props) {
        super(props)
        this.load_state = 0
      }
      load_state = 0
      componentDidMount() {
        console.log('mounted', this.constructor.name, this.load_state)
        this.load_state = 1
        var head = document.getElementsByTagName('head')[0]
        var script = document.createElement('script')
        script.src = this.src
        script.type = 'text/jsx'
        head.append(script);
        window.Babel.transformScriptTags()
      }
      render() {
        if (window[this.name]==this.constructor) {
          setTimeout(() => this.setState({}), 100)
          return null
        }
        else return React.createElement(window[this.name], this.props)
      }
    }
  '''
  for k,v in CLASS_MAP.items():
    yield '''
      var %s = class extends ___UTTPReact_Stub__ {
        name = '%s'
        src = '%s'
      }
    ''' % (k, k, v)
  

