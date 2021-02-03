import './App.css';
import Sidebar from './sidebar';

function App() {

  const title = "Try Title for dynamic value";
  
  return (
    <div className="App">
      <div className="content">
        <h1>{ title }</h1>
      </div>
      <Sidebar/>
    </div>
  );
}

export default App;
