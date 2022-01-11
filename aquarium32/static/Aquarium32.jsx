
const {
  IconButton,
  Toolbar,
  AppBar,
  Icon,
  Typography,
  Drawer,
  Divider,
  List, ListItem, ListItemIcon, ListItemText, 
  FormHelperText,
} = window.MaterialUI;

class Aquarium32 extends React.Component {

  constructor(props) {
    super(props)
    console.log('location.hash', location.hash)
    this.state = {
      drawer_open: false,
      page: location.hash.substring(1) || 'tank',
      width: window.innerWidth,
    }
    window.addEventListener("hashchange", () => {
      this.setState({page: location.hash.substring(1) || 'tank', drawer_open:false})
    }, false);
  }
  
  nav_to(page) {
    location.hash = '#'+page
  }
  
  componentDidMount() {
    window.addEventListener('resize', () => this.setState({width: window.innerWidth}));
  }
  
  render() {

    const always_open = this.state.width > 800;
    const drawer_width = 200;
    
    const page = this.state.page || 'tank';

    const drawer = (
      <div style={{width:drawer_width+'px'}}>
        <img src={__uttpreact__.root+'/fish.jpeg'} style={{width:'100%', minHeight:'130px'}} />
        <List>
          <ListItem button onClick={() => this.nav_to('')} style={{backgroundColor: page=='tank' ? '#f7f7f7' : null}}>
            <ListItemIcon>
              <Icon>tank</Icon>
            </ListItemIcon>
            <ListItemText primary={'Tank'} />
          </ListItem>
          <ListItem button onClick={() => this.nav_to('settings')} style={{backgroundColor: page=='settings' ? '#f7f7f7' : null}}>
            <ListItemIcon>
              <Icon>settings</Icon>
            </ListItemIcon>
            <ListItemText primary={'Settings'} />
          </ListItem>
        </List>
        <Divider />
        <FormHelperText style={{textAlign:'center'}}>{__uttpreact__.version}</FormHelperText>
      </div>
    );

    return (
      <div>
        <AppBar position="fixed">
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={() => this.setState({drawer_open:!this.state.drawer_open})}
            >
              <Icon>menu</Icon>
            </IconButton>
            <Typography variant="h6" noWrap style={{paddingLeft: always_open ? drawer_width-32 : null}}>
              Aquarium32
            </Typography>
          </Toolbar>
        </AppBar>
        <Drawer 
            open={this.state.drawer_open} 
            onClose={() => this.setState({drawer_open:false})}
            variant={always_open ? "permanent" : null}
        >
          {drawer}
        </Drawer>
        <div style={{marginLeft: ((always_open ? drawer_width : 0) + 12)+'px', marginRight:'12px', marginTop:'76px'}}>
          {page=='tank' ? (<Tank />) : null}
          {page=='settings' ? (<Settings />) : null}
        </div>
      </div>
    )
  }
}


