import { Routes,Route } from "react-router-dom";
import AiHomePage from "./Pages/AiHomePage";

function App() {
  return (
    <div>
      <Routes>
        <Route path="/" element={<AiHomePage/>} />
      </Routes>
    </div>
  );
}

export default App;
