
const {
  Button,
  LinearProgress,
  Paper, 
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, 
  Typography,
  Select, MenuItem,
  TextField, 
} = window.MaterialUI;

class Settings extends React.Component {

  constructor(props) {
    super(props)
    this.state = {
      _orig_settings: null,
      _loading: false,
    }
  }
  
  componentDidMount() {
    console.log('componentDidMount')
    this.update()
  }
  
  update() {
    console.log('update')
    this.setState({_loading:true})
    $.getJSON('/settings.json')
    .then(data => {
      var new_state = {_orig_settings:data, _loading:false}
      Object.assign(new_state, data)
      this.setState(new_state)
      });
  }
  
  save() {
    console.log('save')
    this.setState({_loading:true})
    
    var data = {}
    for (const [key, value] of Object.entries(this.state)) {
      if (!key.startsWith('_')) data[key] = value;
    }
    
    $.postJSON('/settings.json', data)
    .then(x => {
      this.setState({_loading:false, _orig_settings:data})
    })
    .catch(err => {
      this.setState({_loading:false})
      alert(err)
    })
  }
  
  reset() {
    this.setState(this.state._orig_settings)
  }
  
  ready() {
    return this.state.num_leds
  }
  
  render() {

    console.log('settings', this.state)
    
    return (
      <div>

        <Typography variant="h1" style={{fontSize:'3rem', lineHeight:'2'}}>
          Settings
          {this.state._loading ? (
            <LinearProgress />
          ) : (
            <IconButton onClick={() => this.update()}>
              <Icon>refresh</Icon>
            </IconButton>
          )}
        </Typography>

        <Typography variant="body2" style={{color:'#800', marginBottom:'1em'}}>
          * Required
        </Typography>

        <Typography variant="body1">
          LED strips typically have either 30 or 144 LEDs per meter.  Waterproof recommended (<a href='https://www.amazon.com/gp/product/B01CDTE83U' target="_blank">example</a>).
        </Typography>

        <Typography variant="body1">
          <TextField
            label={(<span style={{backgroundColor:this.state.num_leds===this.state._orig_settings?.num_leds ? '' : '#FFFF99'}}>Number of LEDs</span>)}
            type="number"
            required
            value={this.state.num_leds}
            defaultValue='1'
            onChange={(e => this.setState({num_leds:parseInt(e.target.value)}))}
          />
        </Typography>

        <Typography variant="body1">
          <br/>
          <Button variant="contained" color="primary" onClick={() => this.save()} disabled={!this.ready()}>
            Save
          </Button>
          <Button variant="" onClick={() => this.reset()} style={{marginLeft:'1em'}}>
            Reset
          </Button>
        </Typography>

        <p>
        </p>
      </div>
    )
  }
}

//            variant={this.state.num_leds==this.state._orig_settings?.num_leds ? 'standard' : 'filled'}

