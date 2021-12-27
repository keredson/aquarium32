import os
import re

import uttp
import json


INCLUDE_JQUERY_STUB = True

CLASS_MAP = None

def init(jsx_path='static'):
  global CLASS_MAP
  CLASS_MAP = {}
  jsx_path = jsx_path.rstrip('/')
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
          CLASS_MAP[m.group(1)] = fn
  print('CLASS_MAP', CLASS_MAP)

#init()



@uttp.get(r'/__uttpreact__')
def __uttpreact__(req):
  yield uttp.header('Content-Type', 'text/javascript')
  yield '''
    function __uttpreact_onload__(start) {
      console.log('__uttpreact_onload__')
  '''
  yield 'var all_classes = ' + json.dumps(list(CLASS_MAP.keys()))
  yield '''
      if (all_classes.every(e => this[e])) {
        console.log('__uttpreact__: all classes loaded')
        start()
      } else {
        setTimeout(() => __uttpreact_onload__(start), 100)
      }
    };
  '''
  if INCLUDE_JQUERY_STUB:
    yield '''
      $ = {
        postJSON: function(path, data) {
          return fetch(path, {
            method: 'post',
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify(data),
          })
        },
        getJSON: function(path) {
          return fetch(path, {
            method: 'get',
          })
          .then(response => response.json())
        },
      }
    '''

