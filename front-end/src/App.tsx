import './App.css';
import Sidebar from './components/sidebar';
import Typography from '@material-ui/core/Typography'
import {BrowserRouter as Router, Route, Switch} from 'react-router-dom'
import Build from './components/pages/build/build';

function App() {

  const title = "Try Title for dynamic value";

  return (
    <Router>
      <div className="App">
        <Switch>
          <Route exact path='/'>
            <Sidebar/>
            <Typography variant='h4'>
              { title }
            </Typography>
          </Route>
          <Route  path='/build'>
           <Build/>
          </Route>
        </Switch>
      </div>
    </Router>
  );
}

export default App;
