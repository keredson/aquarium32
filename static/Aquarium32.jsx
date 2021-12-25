
const {
  IconButton,
  Toolbar,
  AppBar,
  Icon,
  Typography,
  Drawer,
  Divider,
  List, ListItem, ListItemIcon, ListItemText, 
} = window.MaterialUI;

class Aquarium32 extends React.Component {

  constructor(props) {
    super(props)
    this.state = {
      drawer_open: false,
      page: 'home',
    }
  }
  
  render() {

    const drawer = (
      <div style={{minWidth:'240px'}}>
        <div style={{height:'64px'}} />
        <Divider />
        <List>
          <ListItem button onClick={() => this.setState({page:'home'})}>
            <ListItemIcon>
              <Icon>home</Icon>
            </ListItemIcon>
            <ListItemText primary={'Home'} />
          </ListItem>
          <ListItem button onClick={() => this.setState({page:'settings'})}>
            <ListItemIcon>
              <Icon>settings</Icon>
            </ListItemIcon>
            <ListItemText primary={'Settings'} />
          </ListItem>
        </List>
        <Divider />
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
            <Typography variant="h6" noWrap>
              Aquarium32
            </Typography>
          </Toolbar>
        </AppBar>
        <Drawer open={this.state.drawer_open} onClose={() => this.setState({drawer_open:false})}>
          {drawer}
        </Drawer>
        <div style={{margin: '12px', marginTop:'76px'}}>
          {this.state.page=='home' ? (<Home />) : null}
        </div>
      </div>
    )
  }
}


