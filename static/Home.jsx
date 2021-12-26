
const {
  Button,
  LinearProgress,
  Paper, 
  TableContainer, Table, TableHead, TableRow, TableCell, TableBody, 
  Typography,
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
    .then(data => this.setState({tank:data, loading_tank:false}));
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
  
  render() {

    console.log('tank', this.state.tank)
    
    return (
      <div>

        <Typography variant="h4">
          Status
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
                <TableCell>Last Weather Update:</TableCell>
                <TableCell align="right">{this.state.tank ? this.state.tank.last_weather_update : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>GPS:</TableCell>
                <TableCell align="right">{this.state.tank ? (
                  <span>{this.state.tank.lat}, {this.state.tank.lng}</span>
                ) : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>City:</TableCell>
                <TableCell align="right">{this.state.tank ? this.state.tank.city : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Region:</TableCell>
                <TableCell align="right">{this.state.tank ? this.state.tank.region : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Country:</TableCell>
                <TableCell align="right">{this.state.tank ? this.state.tank.country : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Leds:</TableCell>
                <TableCell align="right">{this.state.tank ? this.state.tank.num_leds : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Sun:</TableCell>
                <TableCell align="right">{this.state.tank ? this.render_dict(this.state.tank.sun) : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Moon:</TableCell>
                <TableCell align="right">{this.state.tank ? this.render_dict(this.state.tank.moon) : null}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>When:</TableCell>
                <TableCell align="right">{this.state.tank ? this.state.tank.when : null}</TableCell>
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


