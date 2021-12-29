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

