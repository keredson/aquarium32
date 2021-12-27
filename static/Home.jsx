
const {
  Button,
  LinearProgress,
  Paper, 
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, 
  Typography,
  Select, MenuItem,
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
  
  render_dict(d) {
    if (d==null) return null;
    return (
      <table style={{display:'inline-block'}}><tbody>
        {Object.entries(d).map(x => (
          <tr key={x[0]}><td>{x[0]}:</td><td>{x[1]}</td></tr>
        ))}
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
  
  render() {

    console.log('tank', this.state.tank)
    
    return (
      <div>

        <Typography variant="h4">
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
              <TableRow>
                <TableCell>Sun:</TableCell>
                <TableCell align="right">{this.render_dict(this.state.tank?.sun)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Moon:</TableCell>
                <TableCell align="right">{this.render_dict(this.state.tank?.moon)}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>When:</TableCell>
                <TableCell align="right">{this.state.tank?.when}</TableCell>
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


