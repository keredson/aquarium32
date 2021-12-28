
const {
  Button,
  LinearProgress,
  Paper, 
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, 
  Typography,
  Select, MenuItem,
  Slider,
} = window.MaterialUI;


class Home extends React.Component {

  constructor(props) {
    super(props)
    this.state = {
      tank: null,
      loading_tank: false,
    }
  }
  
  componentDidMount() {
    console.log('componentDidMount')
    this.update()
  }
  
  update() {
    console.log('update')
    this.setState({loading_tank:true})
    fetch('/status.json')
    .then(response => response.json())
    .then(data => {
      this.setState({tank:data, loading_tank:false})
      setTimeout(this.update.bind(this), 60000)
    });
  }
  
  update_sun_state(d) {
    var tank = this.state.tank || {};
    var sun = tank.sun || {};
    Object.assign(sun, d)
    this.setState({tank:tank})
  }
  
  render_cbody(d) {
    if (d==null) return null;
    return (
      <table style={{display:'inline-block'}}><tbody>
        <tr><td>Altitude:</td><td>{Math.round(d['altitude'])}&deg;</td></tr>
        <tr><td>Azimuth:</td><td>{Math.round(d['azimuth'])}&deg;</td></tr>
        {d['radiation'] ? (
          <tr><td>Radiation:</td><td>{Math.round(d['radiation'])} w/m&sup2;</td></tr>
        ) : null}
        {d['fraction'] ? (
          <tr><td>Full:</td><td>{Math.round(100*d['fraction'])}%</td></tr>
        ) : null}
      </tbody></table>
    )
  }
  
  changeTankState(v) {
    console.log('changeTankState', v)
    var tank = this.state.tank
    tank.state = v
    this.setState({tank:tank})
    fetch('/set_state', {method: 'post', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({state:v})})
    .then(response => response.json())
    .then(data => this.setState({tank:data, loading_tank:false}));
  }

  set_sun_state() {
    $.postJSON('/set_sun', {sun:this.state.tank.sun})
    .then(response => response.json())
    .then(sun => {
      this.update_sun_state(sun)
    })
  }
  
  render_sun_controls() {
    return (
      <div style={{padding:'0 1em 1em 1em'}}>
        <Typography id="continuous-slider" gutterBottom>
          Sun
        </Typography>
        <FormHelperText>Radiation: {Math.round(this.state.tank?.sun.radiation)} w/m&sup2;</FormHelperText>
        <FormHelperText>Altitude</FormHelperText>
        <Slider
          min={-180}
          max={180}
          marks={marks}
          value={Math.round(this.state.tank?.sun.altitude)}
          getAriaValueText={(v) => v+'°'}
          track={false}
          onChange={(e,v) => this.update_sun_state({altitude:v})}
          onChangeCommitted={() => this.set_sun_state()}
        />
        <br/>
        <FormHelperText>Azimuth</FormHelperText>
        <Slider
          min={-180}
          max={180}
          marks={marks}
          value={Math.round(this.state.tank?.sun.azimuth)}
          getAriaValueText={(v) => v+'°'}
          track={false}
          onChange={(e,v) => this.update_sun_state({azimuth:v})}
          onChangeCommitted={() => this.set_sun_state()}
        />
      </div>
    )
  }
  
  update_moon_state(d) {
    var tank = this.state.tank || {};
    var moon = tank.moon || {};
    Object.assign(moon, d)
    this.setState({tank:tank})
  }

  set_moon_state() {
    $.postJSON('/set_moon', {moon:this.state.tank.moon})
    .then(moon => {})
  }

  render_moon_controls() {
    return (
      <div style={{padding:'0 1em 1em 1em'}}>
        <Typography id="continuous-slider" gutterBottom>
          Moon
        </Typography>
        <FormHelperText>Phase</FormHelperText>
        <Slider
          min={0}
          max={100}
          marks={marks_moon}
          value={Math.round(100*this.state.tank?.moon.fraction)}
          onChange={(e,v) => this.update_moon_state({fraction:v/100})}
          onChangeCommitted={() => this.set_moon_state()}
        />
        <br/>
        <FormHelperText>Altitude</FormHelperText>
        <Slider
          min={-180}
          max={180}
          marks={marks}
          value={Math.round(this.state.tank?.moon.altitude)}
          getAriaValueText={(v) => v+'°'}
          track={false}
          onChange={(e,v) => this.update_moon_state({altitude:v})}
          onChangeCommitted={() => this.set_moon_state()}
        />
        <br/>
        <FormHelperText>Azimuth</FormHelperText>
        <Slider
          min={-180}
          max={180}
          marks={marks}
          value={Math.round(this.state.tank?.moon.azimuth)}
          getAriaValueText={(v) => v+'°'}
          track={false}
          onChange={(e,v) => this.update_moon_state({azimuth:v})}
          onChangeCommitted={() => this.set_moon_state()}
        />
      </div>
    )
  }
  
  render() {

    console.log('tank', this.state.tank)
    
    return (
      <div>

        <Typography variant="h3">
          Tank
          {this.state.loading_tank ? (
            <LinearProgress />
          ) : (
            <IconButton onClick={() => this.update()}>
              <Icon>refresh</Icon>
            </IconButton>
          )}
        </Typography>

        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label="simple table">
            <TableBody>
              <TableRow>
                <TableCell>Mode:</TableCell>
                <TableCell align="right">
                  <Select
                    value={this.state.tank?.state || 'off'}
                    onChange={(event) => this.changeTankState(event.target.value)}
                  >
                    <MenuItem value={'off'}>Lights Off</MenuItem>
                    <MenuItem value={'full'}>Full Brightness</MenuItem>
                    <MenuItem value={'realtime'}>Realtime</MenuItem>
                    <MenuItem value={'sim_day'}>Simulate 24h</MenuItem>
                    <MenuItem value={'manual'}>Manual</MenuItem>
                  </Select>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Last Weather Update:</TableCell>
                <TableCell align="right">{this.state.tank?.last_weather_update}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>GPS:</TableCell>
                <TableCell align="right">{this.state.tank ? (
                  <span>{this.state.tank.lat}, {this.state.tank.lng}</span>
                ) : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>City:</TableCell>
                <TableCell align="right">{this.state.tank?.city}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Region:</TableCell>
                <TableCell align="right">{this.state.tank?.region}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Country:</TableCell>
                <TableCell align="right">{this.state.tank?.country}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Leds:</TableCell>
                <TableCell align="right">{this.state.tank?.num_leds}</TableCell>
              </TableRow>
              {this.state.tank?.state=='manual' ? (
                <TableRow><TableCell colSpan={2} style={{paddingBottom:'0'}}>
                    {this.render_sun_controls()}
                </TableCell></TableRow>
              ) : (
                <TableRow>
                  <TableCell>Sun:</TableCell>
                  <TableCell align="right">
                    {this.render_cbody(this.state.tank?.sun)}
                  </TableCell>
                </TableRow>
              )}
              {this.state.tank?.state=='manual' ? (
                <TableRow><TableCell colSpan={2} style={{paddingBottom:'0'}}>
                    {this.render_moon_controls()}
                </TableCell></TableRow>
              ) : (
                <TableRow>
                  <TableCell>Moon:</TableCell>
                  <TableCell align="right">
                    {this.render_cbody(this.state.tank?.moon)}
                  </TableCell>
                </TableRow>
              )}
              <TableRow>
                <TableCell>When:</TableCell>
                <TableCell align="right">{this.state.tank?.when} UTC</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>

        <p>
        </p>
      </div>
    )
  }
}


    const marks = []
    for (let step = -180; step <= 180; step+=45) {
      marks.push({
        value: step,
        label: step+'°',
      })
    }

    const marks_radiation = []
    for (let step = 0; step <= 1500; step+=1500) {
      marks_radiation.push({
        value: step,
        label: step+' w/m²',
      })
    }

    const marks_moon = [
      {value: 0, label: 'New'},
      {value: 25, label: 'Crescent'},
      {value: 50, label: 'Half'},
      {value: 75, label: 'Gibbous'},
      {value: 100, label: 'Full'},
    ]

