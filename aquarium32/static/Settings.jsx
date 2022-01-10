
const {
  Button,
  LinearProgress,
  Paper, 
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, 
  Typography,
  Select, MenuItem,
  TextField, FormControlLabel, Switch, FormHelperText,
  Checkbox,
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
    return true
  }
  
  add_strip() {
    var strips = this.state.strips || []
    strips.push({pin:null, leds:null, light_span:null, reversed:false})
    this.setState({strips:strips})
  }
  
  setStripState(i, v) {
    var strips = this.state.strips
    var strip = strips[i]
    Object.assign(strip, v)
    this.setState({strips: strips})
  }
  
  delete_strip(i) {
    var strips = this.state.strips
    strips.splice(i,1)
    this.setState({strips: strips})
  }
  
  render_led_strips() {
    return (
      <div>
        <Typography variant="h4">
          LED Strips
        </Typography>
        
        {this.state.strips?.length ? this.state.strips.map((row, i) => (
          <Paper style={{padding:'1em 1em', marginBottom:'1em'}}>

            <IconButton onClick={() => this.delete_strip(i)} style={{float:'right'}}>
              <Icon>delete</Icon>
            </IconButton>

            <p style={{marginTop:0}}>
              <TextField
                label={(<span >Pin</span>)}
                type="number"
                required
                value={row.pin}
                defaultValue={null}
                onChange={(e => this.setStripState(i, {pin:parseInt(e.target.value)}))}
                helperText="ESP32 digital pin number."
                InputLabelProps={{ shrink: true }}
                placeholder='13'
              />
            </p>
            <p style={{marginTop:0}}>
              <TextField
                label={(<span >LEDs</span>)}
//                type="number"
                inputProps={{ inputMode: 'numeric', pattern:"[0-9]+-?[0-9]*" }}
                value={row.leds}
                defaultValue={null}
                onChange={(e => this.setStripState(i, {leds:e.target.value}))}
//                onChange={(e => console.log('e.target.value', e.target.value))}
                InputLabelProps={{ shrink: true }}
                placeholder='144 or 1-144'
              />
              <FormHelperText>
                The number of LEDs in your strip, or a range (inclusive) if you want to use only a subset.
                LED strips typically have either 30 or 144 LEDs per meter.
              </FormHelperText>
            </p>
            <p>
              <TextField
                label={(<span >Lighting Span (degrees)</span>)}
                type="number"
                value={row.light_span}
                onChange={(e => this.setStripState(i, {light_span:parseInt(e.target.value)}))}
                InputLabelProps={{ shrink: true }}
                placeholder='180'
              />
              <FormHelperText>
                If your lights span the top or a single side, this should be 180°.
                If your lights wrap around three sides, then 270°.
                All four sides, 360°, etc.
              </FormHelperText>
            </p>
            <p style={{marginTop:0}}>
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={row.reversed} onChange={null}
                    onChange={(e => this.setStripState(i, {reversed:e.target.checked}))}
                  />}
                label="Reverse East/West"
              />
              <FormHelperText>
                Depending on tank and LED orientation.
              </FormHelperText>
            </p>
          </Paper>
        )) : (
          <FormHelperText>
            No LED strips set up.  Please add one!
          </FormHelperText>
        )}
        <div style={{marginTop:'.5em'}}>
          <Button variant="contained" onClick={() => this.add_strip()} startIcon={<Icon>add</Icon>}>
            LED Strip
          </Button>
        </div>
      </div>
    )
  }
  
  render() {

    console.log('settings', this.state)
    
    return (
      <div>

        <Typography variant="h3">
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

        {this.render_led_strips()}

        <Typography variant="h4" style={{marginTop:'1em'}}>
          Other Settings
        </Typography>
        
        <Paper style={{padding:'1em 1em'}}>
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
            <TextField
              label={(<span style={{backgroundColor:this.state.max_radiation===this.state._orig_settings?.max_radiation ? '' : '#FFFF99'}}>Maximum Radiation</span>)}
              type='number'
              value={this.state.max_radiation}
              onChange={(e => this.setState({max_radiation:e.target.value}))}
              InputLabelProps={{ shrink: true }}
              placeholder='1500'
            />
            <FormHelperText>
              The amount of solar radiation (in watts/m²) that will max out your lighting.
              Reduce if you find the lighting too dark (esp. in the winter).
            </FormHelperText>
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
            <span style={{width:'8em', display:'inline-block'}}>
              <TextField
                label={(<span style={{backgroundColor:this.state.lat===this.state._orig_settings?.lat ? '' : '#FFFF99'}}>Latitude</span>)}
                value={this.state.lat || ''}
                onChange={(e => this.setState({lat:parseFloat(e.target.value)}))}
                InputLabelProps={{ shrink: true }}
                placeholder='39.8283'
              />
            </span>
            &nbsp;
            <span style={{width:'8em', display:'inline-block'}}>
              <TextField
                label={(<span style={{backgroundColor:this.state.lng===this.state._orig_settings?.lng ? '' : '#FFFF99'}}>Longitude</span>)}
                value={this.state.lng || ''}
                onChange={(e => this.setState({lng:parseFloat(e.target.value)}))}
                InputLabelProps={{ shrink: true }}
                placeholder='-98.5795'
              />
            </span>
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

