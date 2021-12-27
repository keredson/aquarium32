
const {
  Button,
  LinearProgress,
  Paper, 
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, 
  Typography,
  Select, MenuItem,
  TextField, FormControlLabel, Switch, FormHelperText
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

        <Paper style={{padding:'1em 1em'}}>
          <p style={{marginTop:0}}>
            <TextField
              label={(<span style={{backgroundColor:this.state.num_leds===this.state._orig_settings?.num_leds ? '' : '#FFFF99'}}>Number of LEDs</span>)}
              type="number"
              required
              value={this.state.num_leds}
              defaultValue='1'
              onChange={(e => this.setState({num_leds:parseInt(e.target.value)}))}
              helperText="LED strips typically have either 30 or 144 LEDs per meter.  Waterproof recommended."
              InputLabelProps={{ shrink: true }}
              placeholder='144'
            />
          </p>

          <p>
            <TextField
              label={(<span style={{backgroundColor:this.state.sun_color===this.state._orig_settings?.sun_color ? '' : '#FFFF99'}}>Sun Color</span>)}
              value={this.state.sun_color}
              onChange={(e => this.setState({sun_color:e.target.value}))}
              helperText="Typically #FFFFFF (default) or #FFFFDD (more yellow)."
              InputLabelProps={{ shrink: true }}
              placeholder='#FFFFFF'
            />
          </p>

          <p>
            <FormControlLabel
              control={
                <Switch
                  checked={this.state.skip_weather ? null : 'on'}
                  onChange={(e => this.setState({skip_weather:!e.target.checked}))}
                  color="primary"
                />
              }
              label="Simulate Weather"
            />
            <FormHelperText>Simulate cloud cover from localized hourly weather predictions.</FormHelperText>
          </p>

          <p>
            <TextField
              label={(<span style={{backgroundColor:this.state.sim_date===this.state._orig_settings?.sim_date ? '' : '#FFFF99'}}>Simulate Date</span>)}
              value={this.state.sim_date}
              onChange={(e => this.setState({sim_date:e.target.value}))}
              type='date'
              helperText="Lock all simulations to a specific day."
              InputLabelProps={{ shrink: true }}
            />
            <FormHelperText>
              Leave blank (recommended) to simulate sun/moon movements matching the seasons at 
              your location.  Set to make every day's sun/moon movement match a specifc date 
              at your location.
            </FormHelperText>
          </p>

          <p style={{marginBottom:0}}>
            <TextField
              label={(<span style={{backgroundColor:this.state.lat===this.state._orig_settings?.lat ? '' : '#FFFF99'}}>Latitude</span>)}
              value={this.state.lat || ''}
              onChange={(e => this.setState({lat:parseFloat(e.target.value)}))}
              InputLabelProps={{ shrink: true }}
              placeholder='39.8283'
            />
            &nbsp;
            <TextField
              label={(<span style={{backgroundColor:this.state.lng===this.state._orig_settings?.lng ? '' : '#FFFF99'}}>Longitude</span>)}
              value={this.state.lng || ''}
              onChange={(e => this.setState({lng:parseFloat(e.target.value)}))}
              InputLabelProps={{ shrink: true }}
              placeholder='-98.5795'
            />
            <FormHelperText>
              Leave blank (recommended) to automatically detect your location from your IP address.
              (An approximation to your city/town.)
            </FormHelperText>
          </p>

        </Paper>

        <Typography variant="body1">
          <br/>
          <Button variant="contained" color="primary" onClick={() => this.save()} disabled={!this.ready()}>
            Save
          </Button>
          <Button variant="" onClick={() => this.reset()} style={{marginLeft:'1em'}}>
            Reset
          </Button>
        </Typography>


      </div>
    )
  }
}

//            variant={this.state.num_leds==this.state._orig_settings?.num_leds ? 'standard' : 'filled'}

