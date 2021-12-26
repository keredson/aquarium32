try: 
  import urequests

  from urllib.parse import urlencode

  orig_get = urequests.get
  def new_get(url, **kwargs):
    if 'params' in kwargs:
      params = kwargs['params']
      del kwargs['params']
      
      url += '?' + urlencode(params, doseq=True)
      
    return orig_get(url, **kwargs)
    
  urequests.get = new_get

except ImportError as e:
  print('fix_for_urequests: did not find urequests', e)


