import uttp


def start(tank):
  
  @uttp.get(r'/')
  def home():
    print('hello world')
    return 'hello world'
  
  uttp.run_daemon()
  #uttp.run()

